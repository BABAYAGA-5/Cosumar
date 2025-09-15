from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
import os
from .PDF import extract_cv_data, create_pdf_from_docx_template_xml, create_docx_from_template_xml, convert_docx_bytes_to_pdf_bytes
from resume_service.models import Stage, Stagiaire, Sujet
from auth_service.models import Utilisateur
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from .decorators import allow_roles, admin_required, admin_or_rh_required, exclude_utilisateur_role

# Handle CIN module import with fallback
try:
    from .CIN import extract_cin_data
except ImportError:
    try:
        from CIN import extract_cin_data
    except ImportError:
        def extract_cin_data(image_bytes):
            """Fallback function when CIN module is not available"""
            return {}



def get_public_key():
    try:
        with open(settings.BASE_DIR / 'keys' / 'public.pem') as f:
            return f.read()
    except FileNotFoundError:
        return settings.SECRET_KEY

@csrf_exempt
@api_view(['POST'])  # ← ✅ This is the annotation you meant
def upload_pdf(request):
    pdf_file = request.FILES['file']
    pdf_bytes = pdf_file.read()
    return Response({"message": "PDF received", "size": len(pdf_bytes)})

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def domaines(request):
    token = request.headers.get('Authorization')

    return Response({'message': 'Domaines endpoint is working'}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    pass

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exclude_utilisateur_role
def scan_cin(request):
    try:
        cin_file = request.FILES.get('cin')

        if not cin_file:
            return Response({"error": "Fichier CIN manquant."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate extension
        allowed_extensions = ['jpg', 'jpeg', 'png']
        ext = os.path.splitext(cin_file.name)[1].lower().lstrip('.')
        if ext not in allowed_extensions:
            return Response({
                "error": "Type de fichier non autorisé. Veuillez télécharger JPG, JPEG ou PNG.",
                "type": ext
            }, status=status.HTTP_400_BAD_REQUEST)

        # Read file bytes
        cin_bytes = cin_file.read()

        # Extract data
        data = extract_cin_data(cin_bytes)


        if not data or not data.get('cin') or data.get('cin') == 'unknown':
            return Response({
                "message": "CIN scan échoué - aucune donnée valide extraite",
                "data": data
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "CIN scannée avec succès",
            "data": data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": f"CIN processing error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exclude_utilisateur_role
def enregistrer_stagiaire(request):
    """Save new stagiaire with CIN data only (without creating stage)"""
    try:
        nom = request.data.get('nom')
        prenom = request.data.get('prenom')
        cin = request.data.get('cin')
        date_naissance = request.data.get('date_naissance')
        email = request.data.get('email')
        phone = request.data.get('phone')
        introduit_par_id = request.data.get('introduit_par_id')
        
        # Required files for new stagiaire
        cin_file = request.FILES.get('cin_file')

        # Validation for new candidate only
        if not all([nom, prenom, cin, cin_file, email, phone]):
            return Response({
                "error": "Nom, prénom, numéro CIN, fichier CIN, email et téléphone sont requis."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate introduit_par_id if provided
        introduit_par = None
        if introduit_par_id:
            try:
                from auth_service.models import Utilisateur
                introduit_par = Utilisateur.objects.get(id=introduit_par_id)
            except Utilisateur.DoesNotExist:
                return Response({
                    "error": "L'utilisateur spécifié pour 'introduit par' n'existe pas."
                }, status=status.HTTP_400_BAD_REQUEST)

        # Read CIN file
        cin_bytes = cin_file.read()

        parsed_date = None
        if date_naissance:
            try:
                parsed_date = datetime.strptime(date_naissance, "%Y-%m-%d").date()
            except ValueError:
                return Response({
                    "error": "Format de date invalide. Utilisez YYYY-MM-DD."
                }, status=status.HTTP_400_BAD_REQUEST)
            
        # Check if stagiaire already exists
        existing_stagiaire = Stagiaire.objects.filter(matricule=cin).first()
        if existing_stagiaire:
            return Response({
                "error": "Un stagiaire avec ce numéro CIN existe déjà."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create new stagiaire only
        stagiaire = Stagiaire.objects.create(
            nom=nom,
            prenom=prenom,
            matricule=cin,
            date_naissance=parsed_date,
            cin=cin_bytes,
            email=email,
            num_tel=phone,
            introduit_par=introduit_par
        )

        return Response({
            "message": "Nouveau stagiaire créé avec succès! Vous pouvez maintenant créer son stage.",
            "matricule": stagiaire.matricule
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "error": f"Erreur lors de l'enregistrement du stagiaire: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exclude_utilisateur_role
def creer_stage(request):
    """Create stage for any stagiaire (new or existing)"""
    try:
        matricule = request.data.get('matricule')
        
        # Stage fields
        nature = request.data.get('nature')
        date_debut = request.data.get('date_debut')
        date_fin = request.data.get('date_fin')
        sujet_id = request.data.get('sujet_id')
        status_stage = request.data.get('status', 'stage_created')
        introduit_par_id = request.data.get('introduit_par_id')  # Optional introducer user ID
        
        # Required files for stage
        cv_file = request.FILES.get('cv_file')
        assurance_file = request.FILES.get('assurance_file')
        convention_file = request.FILES.get('convention_file')
        lettre_motivation_file = request.FILES.get('lettre_motivation_file')

        # Validation
        if not all([matricule, cv_file, nature, date_debut, date_fin]):
            return Response({
                "error": "Matricule, CV et informations de stage sont requis."
            }, status=status.HTTP_400_BAD_REQUEST)

        if date_debut > date_fin:
            return Response({
                "error": "La date de début doit être antérieure à la date de fin."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if stagiaire exists
        stagiaire = Stagiaire.objects.filter(matricule=matricule, deleted=False).first()
        if not stagiaire:
            return Response({
                "error": "Stagiaire non trouvé. Vous devez d'abord créer le stagiaire."
            }, status=status.HTTP_404_NOT_FOUND)

        if Stage.objects.filter(stagiaire=stagiaire, deleted=False, statut__in=['en_attente_visite_medicale', 'en_attente_depot_dossier','en_attente_des_signatures', 'stage_en_cours', 'en_attente_depot_rapport','en_attente_signature_du_rapport_par_l_encadrant']).exists():
            return Response({
                "error": "Un stage avec un statut en attente existe déjà pour ce stagiaire."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Capacity validation for the user who brought the stagiaire (introducer)
        introduit_par_user = None
        if introduit_par_id:
            try:
                introduit_par_user = Utilisateur.objects.get(id=introduit_par_id)
                
                # Check if the introducer's capacite_cache_restante is less than capacite_cache
                if introduit_par_user.capacite_cache_restante >= introduit_par_user.capacite_cache:
                    return Response({
                        "error": f"L'utilisateur {introduit_par_user.prenom} {introduit_par_user.nom} a atteint sa capacité maximale de stagiaires introduits ({introduit_par_user.capacite_cache})."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except Utilisateur.DoesNotExist:
                return Response({
                    "error": "L'utilisateur qui a introduit le stagiaire n'existe pas."
                }, status=status.HTTP_404_NOT_FOUND)

        


        if assurance_file and convention_file:
            statut_stage = 'en_attente_visite_medicale'
        else:
            statut_stage = 'en_attente_depot_dossier'

        # Parse stage dates
        parsed_date_debut = None
        parsed_date_fin = None
        try:
            if date_debut:
                parsed_date_debut = datetime.strptime(date_debut, "%Y-%m-%d").date()
            if date_fin:
                parsed_date_fin = datetime.strptime(date_fin, "%Y-%m-%d").date()
        except ValueError:
            return Response({
                "error": "Format de date invalide pour les dates de stage. Utilisez YYYY-MM-DD."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get sujet if provided
        sujet = None
        sujet_creator = None
        if sujet_id:
            try:
                sujet = Sujet.objects.get(id=sujet_id, deleted=False)
                sujet_creator = sujet.created_by
                
                # Check if the sujet creator's capacite_restante is less than capacite
                if sujet_creator.capacite_restante >= sujet_creator.capacite:
                    return Response({
                        "error": f"L'utilisateur qui a créé le sujet ({sujet_creator.prenom} {sujet_creator.nom}) a atteint sa capacité maximale de sujets ({sujet_creator.capacite})."
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Sujet.DoesNotExist:
                return Response({
                    "error": "Sujet sélectionné non trouvé."
                }, status=status.HTTP_400_BAD_REQUEST)

        # Create new stage for the stagiaire
        try:
            stage = Stage.objects.create(
                stagiaire=stagiaire,
                nature=nature,
                date_debut=parsed_date_debut,
                date_fin=parsed_date_fin,
                sujet=sujet,
                introduit_par=introduit_par_user,  # Set the introducer
                cv=cv_file.read() if cv_file else None,
                convention=convention_file.read() if convention_file else None,
                assurance=assurance_file.read() if assurance_file else None,
                lettre_motivation=lettre_motivation_file.read() if lettre_motivation_file else None,
                statut=statut_stage
            )
        except ValidationError as e:
            return Response({
                "error": str(e.message) if hasattr(e, 'message') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        # Increment capacities after successful stage creation
        if introduit_par_user:
            introduit_par_user.capacite_cache_restante += 1
            introduit_par_user.save()
            
        if sujet_creator:
            sujet_creator.capacite_restante += 1
            sujet_creator.save()

        # Generate PDF demande de stage from DOCX template
        try:
            # Load DOCX template
            docx_template_path = os.path.join(settings.BASE_DIR, 'resume_service', 'media', 'DEMANDE DE STAGE.docx')
            
            if os.path.exists(docx_template_path):
                # Prepare replacements dictionary
                replacements = {
                    '«NOM»': stagiaire.nom.upper() if stagiaire.nom else '',
                    '«PRENOM»': stagiaire.prenom.title() if stagiaire.prenom else '',
                    '«CIN»': stagiaire.matricule if stagiaire.matricule else '',
                    '«EMAIL»': stagiaire.email if stagiaire.email else '',
                    '«TELEPHONE»': stagiaire.num_tel if stagiaire.num_tel else '',
                    '«DATE_NAISSANCE»': stagiaire.date_naissance.strftime('%d/%m/%Y') if stagiaire.date_naissance else '',
                    '«NATURE»': stage.nature.upper() if stage.nature else '',
                    '«DATE_DEBUT»': stage.date_debut.strftime('%d/%m/%Y') if stage.date_debut else '',
                    '«DATE_FIN»': stage.date_fin.strftime('%d/%m/%Y') if stage.date_fin else '',
                    '«PERIODE_DU»': stage.date_debut.strftime('%d/%m/%Y') if stage.date_debut else '',
                    '«PERIODE_AU»': stage.date_fin.strftime('%d/%m/%Y') if stage.date_fin else '',
                    '«PERIODE_ACCORDEE_DU»': stage.date_debut.strftime('%d/%m/%Y') if stage.date_debut else '',
                    '«PERIODE_ACCORDEE_AU»': stage.date_fin.strftime('%d/%m/%Y') if stage.date_fin else '',
                    '«SUJET»': sujet.titre if sujet and sujet.titre else '',
                    '«DESCRIPTION_SUJET»': sujet.description if sujet and sujet.description else '',
                    '«DATE_DEMANDE»': datetime.now().strftime('%d/%m/%Y'),
                    '«SPECIALITE»': '',
                    '«ETABLISSEMENT»': '',
                    '«DIRECTION»': '',
                    '«ENCADRANT»': '',
                    '«SERVICE»': '',
                    '«NOM_ENCADRANT»': '',
                    '«DATE_SIGNATURE_ENCADRANT»': '',
                    '«SIGNATURE_ENCADRANT»': '',
                    '«NOM_RESPONSABLE_SERVICE»': '',
                    '«DATE_SIGNATURE_RESPONSABLE_SERVICE»': '',
                    '«DATE_SIGNATURE_RH»': ''
                }
                
                filled_docx_bytes = create_docx_from_template_xml(
                    docx_path=docx_template_path,
                    replacements=replacements
                )
                
                if filled_docx_bytes:
                    stage.demande_de_stage = filled_docx_bytes
                    
                    # Convert DOCX to PDF and cache it
                    try:
                        pdf_bytes = convert_docx_bytes_to_pdf_bytes(filled_docx_bytes)
                        if pdf_bytes:
                            stage.demande_de_stage_pdf = pdf_bytes
                    except Exception:
                        pass  # PDF will be generated on-demand if conversion fails
                    
                    stage.save()
                    
            else:
                pass  # Template not found, skip PDF generation
                
        except Exception:
            pass  # Don't fail stage creation if PDF generation fails

        # Determine success message based on status
        if status_stage == 'dossier_complete':
            message = "Stage créé et dossier complété avec succès!"
        else:
            message = "Stage créé avec succès!"

        return Response({
            "message": message,
            "matricule": stagiaire.matricule,
            "stage_id": stage.id,
            "status": statut_stage
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "error": f"Erreur lors de la création du stage: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chercher_stagiaires(request):
    """Search for existing stagiaires"""
    try:
        search_query = request.GET.get('search', '').strip()
        
        # Search in nom, prenom, matricule fields and concatenated "prenom nom"
        stagiaires_queryset = Stagiaire.objects.filter(deleted=False)
        
        # Role-based filtering: users with 'utilisateur' role can only see stagiaires with stages having sujets they created
        current_user = request.user
        if hasattr(current_user, 'role') and current_user.role == 'utilisateur':
            # Only show stagiaires that have stages with sujets created by this user
            stagiaires_queryset = stagiaires_queryset.filter(
                stages__sujet__created_by=current_user,
                stages__sujet__isnull=False
            ).distinct()
        
        stagiaires = stagiaires_queryset.annotate(
            full_name=Concat('prenom', Value(' '), 'nom', output_field=CharField())
        ).filter(
            Q(nom__icontains=search_query) |
            Q(prenom__icontains=search_query) |
            Q(matricule__icontains=search_query) |
            Q(full_name__icontains=search_query)
        ).values(
            'matricule', 'nom', 'prenom', 'date_naissance', 'email'
        ).order_by('nom', 'prenom')[:25]
        
        return Response(list(stagiaires), status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": f"Erreur lors de la recherche des stagiaires: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidate_documents(request, matricule):
    """Get candidate documents from their latest stage"""
    try:
        # Get the latest stage for this candidate
        latest_stage = Stage.objects.filter(
            stagiaire__matricule=matricule,
            deleted=False
        ).order_by('-created_at').first()
        
        if not latest_stage:
            return Response({
                "success": False,
                "message": "Aucun stage trouvé pour ce stagiaire"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Prepare document info
        documents = {}
        cv_data = {}
        
        # Get CV file and data
        if latest_stage.cv:
            documents['cv_file'] = f"cv_stagiaire_{matricule}.pdf"
            documents['has_cv'] = True
            
        # Get CIN file from stagiaire (stored in Stagiaire model)
        if latest_stage.stagiaire.cin:
            documents['cin_file'] = f"cin_stagiaire_{matricule}.jpg"
            documents['has_cin'] = True
            
        # Get CV extracted data (email, phone) from stagiaire
        if latest_stage.stagiaire.email:
            cv_data['email'] = latest_stage.stagiaire.email
        if latest_stage.stagiaire.num_tel:
            cv_data['phone'] = latest_stage.stagiaire.num_tel
            
        return Response({
            "success": True,
            "documents": documents,
            "cv_data": cv_data if cv_data else None,
            "stage_id": latest_stage.id
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "success": False,
            "error": f"Erreur lors de la récupération des documents: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chercher_sujets(request):
    """Search for existing sujets"""
    try:
        search_query = request.GET.get('search', '').strip()
        
        
        # Search in titre and description fields
        sujets = Sujet.objects.filter(
            deleted=False
        ).filter(
            Q(titre__icontains=search_query) |
            Q(description__icontains=search_query)
        ).values(
            'id', 'titre', 'description'
        ).order_by('titre')[:10]

        return Response(list(sujets), status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": f"Erreur lors de la recherche des sujets: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chercher_stages(request):
    """Search for existing stages"""
    try:
        nature = request.GET.get('nature', '').strip()
        stagiaire_nom = request.GET.get('stagiaire_nom', '').strip()
        stagiaire_prenom = request.GET.get('stagiaire_prenom', '').strip()
        date_debut = request.GET.get('date_debut', '').strip()
        date_fin = request.GET.get('date_fin', '').strip()
        statut = request.GET.get('statut', '').strip()
        sujet_titre = request.GET.get('sujet', '').strip()
        created_at = request.GET.get('created_at', '').strip()

        # Build filters dynamically
        filters = {"deleted": False}

        if nature:
            filters["nature__icontains"] = nature
        if stagiaire_nom:
            filters["stagiaire__nom__icontains"] = stagiaire_nom
        if stagiaire_prenom:
            filters["stagiaire__prenom__icontains"] = stagiaire_prenom
        if date_debut:
            filters["date_debut__icontains"] = date_debut
        if date_fin:
            filters["date_fin__icontains"] = date_fin
        if statut:
            filters["statut__icontains"] = statut
        if sujet_titre:
            filters["sujet__titre__icontains"] = sujet_titre
        if created_at:
            filters["created_at__icontains"] = created_at

        # Role-based filtering: 
        # - users with 'utilisateur' role can only see stages with sujets they created
        # - users with 'responsable_de_service' role can see stages with sujets created by utilisateurs in their same department
        current_user = request.user
        if hasattr(current_user, 'role') and current_user.role == 'utilisateur':
            # Only show stages that have sujets created by this user
            filters["sujet__created_by"] = current_user
            # Also ensure the stage has a sujet (not null)
            filters["sujet__isnull"] = False
        elif hasattr(current_user, 'role') and current_user.role == 'responsable_de_service':
            # Show stages where sujet was created by any utilisateur in the same department
            if current_user.departement:
                # Get all utilisateurs in the same department
                from auth_service.models import Utilisateur
                utilisateurs_meme_departement = Utilisateur.objects.filter(
                    departement=current_user.departement,
                    role='utilisateur',
                    is_active=True
                )
                # Filter stages to show only those with sujets created by these utilisateurs
                filters["sujet__created_by__in"] = utilisateurs_meme_departement
                # Also ensure the stage has a sujet (not null)
                filters["sujet__isnull"] = False
            else:
                # If no department assigned, only show stages they created (fallback to utilisateur behavior)
                filters["sujet__created_by"] = current_user
                filters["sujet__isnull"] = False

        # Get stages with all related data
        stages_queryset = Stage.objects.filter(**filters).select_related('stagiaire', 'sujet', 'introduit_par').order_by('-created_at')
        
        stages_data = []
        for stage in stages_queryset:
            stage_data = {
                'id': stage.id,
                'nature': stage.nature,
                'date_debut': stage.date_debut.strftime('%Y-%m-%d') if stage.date_debut else None,
                'date_fin': stage.date_fin.strftime('%Y-%m-%d') if stage.date_fin else None,
                'statut': stage.statut,
                'created_at': stage.created_at.strftime('%Y-%m-%d %H:%M:%S') if stage.created_at else None,
                'stagiaire': {
                    'matricule': stage.stagiaire.matricule if stage.stagiaire else None,
                    'nom': stage.stagiaire.nom if stage.stagiaire else '',
                    'prenom': stage.stagiaire.prenom if stage.stagiaire else '',
                } if stage.stagiaire else None,
                'sujet': {
                    'id': stage.sujet.id if stage.sujet else None,
                    'titre': stage.sujet.titre if stage.sujet else None,
                } if stage.sujet else None,
                'introduit_par': {
                    'id': stage.introduit_par.id if stage.introduit_par else None,
                    'nom': stage.introduit_par.nom if stage.introduit_par else '',
                    'prenom': stage.introduit_par.prenom if stage.introduit_par else '',
                    'email': stage.introduit_par.email if stage.introduit_par else '',
                    'departement': stage.introduit_par.departement if stage.introduit_par else '',
                } if stage.introduit_par else None
            }
            stages_data.append(stage_data)

        return Response({
            "stages": stages_data,
            "count": len(stages_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": f"Erreur lors de la recherche des stages: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            "error": f"Erreur lors de la recherche des stages: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_cv(request):
    """Process the uploaded CV data"""
    try:
        cv_file = request.FILES.get('cv')

        if not cv_file:
            return Response({"error": "Fichier CV manquant."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate extension
        allowed_extensions = ['pdf']
        ext = os.path.splitext(cv_file.name)[1].lower().lstrip('.')
        if ext not in allowed_extensions:
            return Response({
                "error": "Type de fichier non autorisé. Veuillez télécharger un fichier PDF.",
                "type": ext
            }, status=status.HTTP_400_BAD_REQUEST)

        # Read file bytes
        cv_bytes = cv_file.read()

        data = extract_cv_data(cv_bytes)

        return Response({"status": "success", "data": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return {"status": "error", "message": str(e)}


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recuperer_stage(request, stage_id):
    """Retrieve a single stage by ID passed as request parameter"""
    try:
        if not stage_id:
            return Response(
                {"error": "Stage ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        stage = Stage.objects.select_related("stagiaire", "sujet").filter(id=stage_id).first()

        if not stage:
            return Response(
                {"error": "Stage not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        data = {
            "id": stage.id,
            "nature": stage.nature,
            "statut": stage.statut,
            "date_debut": stage.date_debut.strftime('%Y-%m-%d') if stage.date_debut else None,
            "date_fin": stage.date_fin.strftime('%Y-%m-%d') if stage.date_fin else None,
            "prolongation": stage.prolongation.strftime('%Y-%m-%d') if stage.prolongation else None,
            "created_at": stage.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": stage.updated_at.strftime('%Y-%m-%d %H:%M:%S'),

            "stagiaire": {
                "matricule": stage.stagiaire.matricule,
                "prenom": stage.stagiaire.prenom,
                "nom": stage.stagiaire.nom,
                "email": stage.stagiaire.email,
                "num_tel": stage.stagiaire.num_tel,
                "date_naissance": stage.stagiaire.date_naissance.strftime('%Y-%m-%d') if stage.stagiaire.date_naissance else None,
            } if stage.stagiaire else None,

            # sujet info
            "sujet": {
                "id": stage.sujet.id,
                "titre": stage.sujet.titre,
                "description": stage.sujet.description,
                "created_by": stage.sujet.created_by.id if stage.sujet.created_by else None
            } if stage.sujet else None
        }

        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@exclude_utilisateur_role
def update_stage(request, stage_id):
    """Update a stage by ID"""
    try:
        if not stage_id:
            return Response(
                {"error": "Stage ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        stage = Stage.objects.select_related("stagiaire").filter(id=stage_id, deleted=False).first()

        if not stage:
            return Response(
                {"error": "Stage not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get update data from request
        data = request.data
        
        # Update stage fields
        if 'nature' in data:
            stage.nature = data['nature']
        if 'date_debut' in data:
            try:
                stage.date_debut = datetime.strptime(data['date_debut'], '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format for date_debut. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        if 'date_fin' in data:
            try:
                stage.date_fin = datetime.strptime(data['date_fin'], '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format for date_fin. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        if 'statut' in data:
            stage.statut = data['statut']
        if 'prolongation' in data:
            if data['prolongation']:
                try:
                    stage.prolongation = datetime.strptime(data['prolongation'], '%Y-%m-%d').date()
                except ValueError:
                    return Response({"error": "Invalid date format for prolongation. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                stage.prolongation = None

        # Update stagiaire fields if provided
        if 'stagiaire' in data:
            stagiaire_data = data['stagiaire']
            if 'nom' in stagiaire_data:
                stage.stagiaire.nom = stagiaire_data['nom']
            if 'prenom' in stagiaire_data:
                stage.stagiaire.prenom = stagiaire_data['prenom']
            if 'email' in stagiaire_data:
                stage.stagiaire.email = stagiaire_data['email']
            if 'num_tel' in stagiaire_data:
                stage.stagiaire.num_tel = stagiaire_data['num_tel']
            if 'date_naissance' in stagiaire_data:
                try:
                    stage.stagiaire.date_naissance = datetime.strptime(stagiaire_data['date_naissance'], '%Y-%m-%d').date()
                except ValueError:
                    return Response({"error": "Invalid date format for date_naissance. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
            
            stage.stagiaire.save()

        # Save stage
        stage.save()

        return Response({
            "success": True,
            "message": "Stage updated successfully",
            "stage_id": stage.id
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cin(request, matricule):
    """Get CIN document for a stagiaire by matricule"""
    try:
        stagiaire = Stagiaire.objects.filter(matricule=matricule, deleted=False).first()
        
        if not stagiaire:
            return Response(
                {"error": "Stagiaire not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        if not stagiaire.cin:
            return Response(
                {"error": "CIN document not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        from django.http import HttpResponse
        response = HttpResponse(stagiaire.cin, content_type='image/jpeg')
        response['Content-Disposition'] = f'inline; filename="cin_{matricule}.jpg"'
        return response
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stage_document(request, stage_id, document_type):
    """Get stage document by stage ID and document type"""
    try:
        stage = Stage.objects.filter(id=stage_id, deleted=False).first()
        
        if not stage:
            return Response(
                {"error": "Stage not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Role-based access control: Check if user can access this stage
        current_user = request.user
        can_access = False
        
        if hasattr(current_user, 'role'):
            if current_user.role in ['admin', 'admin_rh', 'utilisateur_rh']:
                # RH and admin roles can access all stages
                can_access = True
            elif current_user.role == 'utilisateur':
                # Utilisateur can only access stages with sujets they created
                if stage.sujet and stage.sujet.created_by == current_user:
                    can_access = True
            elif current_user.role == 'responsable_de_service':
                # Responsable de service can access stages from their department
                if stage.sujet and stage.sujet.created_by and current_user.departement:
                    if stage.sujet.created_by.departement == current_user.departement and stage.sujet.created_by.role == 'utilisateur':
                        can_access = True
        
        if not can_access:
            return Response(
                {"error": "Vous n'avez pas l'autorisation d'accéder à ce document"},
                status=status.HTTP_403_FORBIDDEN
            )
        

            
        document_data = None
        content_type = 'application/pdf'
        filename_prefix = document_type
        
        if document_type == 'cv' and stage.cv:
            document_data = stage.cv
        elif document_type == 'convention' and stage.convention:
            document_data = stage.convention
        elif document_type == 'assurance' and stage.assurance:
            document_data = stage.assurance
        elif document_type == 'lettre_motivation' and stage.lettre_motivation:
            document_data = stage.lettre_motivation
        elif document_type == 'demande_de_stage' and stage.demande_de_stage:
            # First, try to serve cached PDF if available
            if stage.demande_de_stage_pdf:
                document_data = stage.demande_de_stage_pdf
            else:
                # Convert stored DOCX to PDF and cache it
                pdf_data = convert_docx_bytes_to_pdf_bytes(stage.demande_de_stage)
                if pdf_data:
                    # Cache the PDF for future requests
                    stage.demande_de_stage_pdf = pdf_data
                    stage.save()
                    document_data = pdf_data
                else:
                    return Response(
                        {"error": "Failed to convert demande de stage to PDF"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
        else:
            return Response(
                {"error": f"Document '{document_type}' not found"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        from django.http import HttpResponse
        response = HttpResponse(document_data, content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{filename_prefix}_{stage_id}.pdf"'
        return response
        
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@exclude_utilisateur_role
def upload_stage_document(request, stage_id):
    """
    Upload documents for a specific stage
    """
    try:
        stage = Stage.objects.get(id=stage_id)
        
        # Check if user has permission to update this stage
        if hasattr(request.user, 'stagiaire') and stage.stagiaire != request.user.stagiaire:
            return Response(
                {"error": "You don't have permission to update this stage"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Handle different document types
        updated_fields = []
        
        if 'convention' in request.FILES:
            stage.convention = request.FILES['convention'].read()
            updated_fields.append('convention')
            
        if 'assurance' in request.FILES:
            stage.assurance = request.FILES['assurance'].read()
            updated_fields.append('assurance')
            
        if 'lettre_motivation' in request.FILES:
            stage.lettre_motivation = request.FILES['lettre_motivation'].read()
            updated_fields.append('lettre_motivation')
            
        if 'demande_de_stage' in request.FILES:
            stage.demande_de_stage = request.FILES['demande_de_stage'].read()
            updated_fields.append('demande_de_stage')
        
        if not updated_fields:
            return Response(
                {"error": "No valid document files provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if all required documents are now present
        has_convention = stage.convention is not None
        has_assurance = stage.assurance is not None
        has_lettre_motivation = stage.lettre_motivation is not None
        has_demande_de_stage = stage.demande_de_stage is not None
        
        # Update status if all documents are uploaded
        if has_convention and has_assurance and has_lettre_motivation and has_demande_de_stage:
            stage.statut = 'en_attente_validation'
        
        stage.save()
        
        return Response({
            "message": f"Documents uploaded successfully: {', '.join(updated_fields)}",
            "updated_fields": updated_fields,
            "status": stage.statut
        }, status=status.HTTP_200_OK)
        
    except Stage.DoesNotExist:
        return Response(
            {"error": "Stage not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_stagiaires(request):
    """Get paginated stagiaires for admin/admin_rh users with filtering support"""
    try:
        # Get pagination parameters
        page_number = request.GET.get('page', 1)
        page_size = int(request.GET.get('page_size', 25))
        
        # Get filter parameters
        search_term = request.GET.get('search', '').strip()
        stage_status = request.GET.get('stage_status', '').strip()
        stage_nature = request.GET.get('stage_nature', '').strip()
        has_active_stage = request.GET.get('has_active_stage', '').strip()
        
        stagiaires_queryset = Stagiaire.objects.filter(deleted=False)
        
        # Role-based filtering: users with 'utilisateur' role can only see stagiaires with stages having sujets they created
        current_user = request.user
        if hasattr(current_user, 'role') and current_user.role == 'utilisateur':
            # Only show stagiaires that have stages with sujets created by this user
            stagiaires_queryset = stagiaires_queryset.filter(
                stages__sujet__created_by=current_user,
                stages__sujet__isnull=False
            ).distinct()
        
        # Apply search filter if provided
        if search_term:
            stagiaires_queryset = stagiaires_queryset.filter(
                Q(matricule__icontains=search_term) |
                Q(nom__icontains=search_term) |
                Q(prenom__icontains=search_term) |
                Q(email__icontains=search_term)
            )
        
        # Apply stage-based filters by joining with Stage model
        if stage_status or stage_nature or has_active_stage:
            if has_active_stage == 'true':
                # Only stagiaires with active stages
                stage_filter = Q(stages__isnull=False)
                
                # Apply additional stage filters to the latest stage
                if stage_status:
                    stage_filter &= Q(stages__statut=stage_status)
                if stage_nature:
                    stage_filter &= Q(stages__nature=stage_nature)
                
                stagiaires_queryset = stagiaires_queryset.filter(stage_filter).distinct()
                    
            elif has_active_stage == 'false':
                # Only stagiaires without stages
                stagiaires_queryset = stagiaires_queryset.filter(stages__isnull=True)
            else:
                # All stagiaires - apply stage filters only to those who have stages
                stage_conditions = []
                
                if stage_status:
                    stage_conditions.append(Q(stages__statut=stage_status))
                if stage_nature:
                    stage_conditions.append(Q(stages__nature=stage_nature))
                
                if stage_conditions:
                    # Combine stage conditions with AND
                    combined_stage_filter = stage_conditions[0]
                    for condition in stage_conditions[1:]:
                        combined_stage_filter &= condition
                    
                    # Filter: (no stages) OR (has stages with specified conditions)
                    stagiaires_queryset = stagiaires_queryset.filter(
                        Q(stages__isnull=True) | combined_stage_filter
                    ).distinct()
        
        # Order by creation date
        stagiaires_queryset = stagiaires_queryset.order_by('date_creation')
        
        total_count = stagiaires_queryset.count()
        
        paginator = Paginator(stagiaires_queryset, page_size)
        
        try:
            stagiaires_page = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            stagiaires_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page
            stagiaires_page = paginator.page(paginator.num_pages)
        
        # Build response data
        stagiaires_data = []
        for stagiaire in stagiaires_page:
            # Get latest stage for this stagiaire
            latest_stage = Stage.objects.filter(stagiaire=stagiaire).order_by('-created_at').first()
            
            stagiaires_data.append({
                'matricule': stagiaire.matricule,
                'nom': stagiaire.nom,
                'prenom': stagiaire.prenom,
                'email': stagiaire.email,
                'num_tel': stagiaire.num_tel,
                'date_naissance': stagiaire.date_naissance,
                'created_at': stagiaire.date_creation,
                'updated_at': stagiaire.date_creation,  # Using date_creation since there's no updated field
                'latest_stage_status': latest_stage.statut if latest_stage else None,
                'latest_stage_nature': latest_stage.nature if latest_stage else None,
                'has_active_stage': latest_stage is not None
            })
        
        # Return paginated response
        return Response({
            'results': stagiaires_data,
            'count': paginator.count,
            'page': stagiaires_page.number,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'has_next': stagiaires_page.has_next(),
            'has_previous': stagiaires_page.has_previous(),
            'next_page_number': stagiaires_page.next_page_number() if stagiaires_page.has_next() else None,
            'previous_page_number': stagiaires_page.previous_page_number() if stagiaires_page.has_previous() else None
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': 'Erreur lors de la récupération des stagiaires'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats_counts(request):
    """
    Retourne le nombre de sujets, stagiaires et candidatures (stages).
    Ajoute le nombre de stagiaires avec un stage terminé pour chaque année des 5 dernières années.
    Génère automatiquement les statistiques pour tous les départements disponibles.
    """
    try:
        
        # Get all department choices dynamically from the model
        department_choices = [choice[0] for choice in Utilisateur._meta.get_field('departement').choices]
        
        # Generate statistics for all departments dynamically
        departements_stats = {}
        for dept_code in department_choices:
            count = Stage.objects.filter(
                deleted=False,
                statut='stage_en_cours',
                sujet__created_by__departement=dept_code
            ).count()
            
            # Create a readable name for the department
            dept_name = dict(Utilisateur._meta.get_field('departement').choices).get(dept_code, dept_code)
            departements_stats[f"nb_stagiaires_dep_{dept_code}"] = {
                "count": count,
                "department_name": dept_name,
                "department_code": dept_code
            }

        nb_sujets = Sujet.objects.filter(deleted=False).count()
        nb_stagiaires = Stagiaire.objects.filter(deleted=False).count()
        nb_stage_en_cours = Stage.objects.filter(
            deleted=False,
            statut='stage_en_cours'
        ).count()
        nb_stage_en_attante_vm = Stage.objects.filter(
            deleted=False,
            statut='en_attente_visite_medicale'
        ).count() 
        
        # Calcul du nombre de stagiaires avec un stage "Terminé" pour chaque année des 5 dernières années
        current_year = datetime.now().year
        stagiaires_termine_par_annee = []
        for year in range(current_year - 4, current_year + 1):
            count = Stagiaire.objects.filter(
                deleted=False,
                stages__statut='termine',
                stages__date_fin__year=year
            ).distinct().count()
            stagiaires_termine_par_annee.append({
                "annee": year,
                "nb_stagiaires_termine": count
            })

        # Get stage nature choices dynamically
        stage_nature_choices = [choice[0] for choice in Stage._meta.get_field('nature').choices]
        
        # Generate statistics for all stage natures dynamically
        stages_par_nature = {}
        for nature_code in stage_nature_choices:
            count = Stage.objects.filter(
                deleted=False,
                nature=nature_code,
                date_debut__year=current_year
            ).count()
            
            # Create a readable name for the nature
            nature_name = dict(Stage._meta.get_field('nature').choices).get(nature_code, nature_code)
            stages_par_nature[f"nb_{nature_code}"] = {
                "count": count,
                "nature_name": nature_name,
                "nature_code": nature_code
            }

        # Get stage status choices dynamically
        stage_status_choices = [choice[0] for choice in Stage._meta.get_field('statut').choices]
        
        # Generate stages par département with status breakdown
        stages_par_departement = {}
        for dept_code in department_choices:
            dept_name = dict(Utilisateur._meta.get_field('departement').choices).get(dept_code, dept_code)
            
            # Get total count for this department
            total_count = Stage.objects.filter(
                deleted=False,
                sujet__created_by__departement=dept_code
            ).count()
            
            # Get count by status for this department
            status_breakdown = {}
            for status_code in stage_status_choices:
                status_count = Stage.objects.filter(
                    deleted=False,
                    statut=status_code,
                    sujet__created_by__departement=dept_code
                ).count()
                
                status_name = dict(Stage._meta.get_field('statut').choices).get(status_code, status_code)
                status_breakdown[status_code] = {
                    "count": status_count,
                    "status_name": status_name
                }
            
            stages_par_departement[dept_code] = {
                "department_name": dept_name,
                "department_code": dept_code,
                "total_stages": total_count,
                "status_breakdown": status_breakdown
            }

        # Prepare response with both old format (for backward compatibility) and new dynamic format
        response_data = {
            "nb_sujets": nb_sujets,
            "nb_stagiaires": nb_stagiaires,
            "nb_stage_en_cours": nb_stage_en_cours,
            "nb_stage_en_attante_vm": nb_stage_en_attante_vm,
            "stagiaires_termine_par_annee": stagiaires_termine_par_annee,
            
            # Dynamic department statistics
            "departements_stats": departements_stats,
            "available_departments": [
                {
                    "code": choice[0],
                    "name": choice[1]
                } for choice in Utilisateur._meta.get_field('departement').choices
            ],
            
            # Dynamic stage nature statistics
            "stages_par_nature": stages_par_nature,
            "available_stage_natures": [
                {
                    "code": choice[0],
                    "name": choice[1]
                } for choice in Stage._meta.get_field('nature').choices
            ],
            
            # Stages par département with status breakdown
            "stages_par_departement": stages_par_departement,
            "available_stage_statuses": [
                {
                    "code": choice[0],
                    "name": choice[1]
                } for choice in Stage._meta.get_field('statut').choices
            ]
        }
        
        # Add backward compatibility for existing frontend code
        if departements_stats:
            # Add individual department counts for backward compatibility
            for dept_key, dept_data in departements_stats.items():
                response_data[dept_key] = dept_data["count"]
                
        if stages_par_nature:
            # Add individual stage nature counts for backward compatibility
            for nature_key, nature_data in stages_par_nature.items():
                response_data[nature_key] = nature_data["count"]
            
            # Map to old field names for backward compatibility
            response_data["nb_stage"] = stages_par_nature.get("nb_stage_observation", {}).get("count", 0)
            response_data["nb_alternance"] = stages_par_nature.get("nb_stage_application", {}).get("count", 0)
            response_data["nb_pfe"] = stages_par_nature.get("nb_pfe", {}).get("count", 0)

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": f"Erreur lors du calcul des statistiques: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@allow_roles('utilisateur', 'responsable_de_service')
def sign_demande_stage(request, stage_id):
    """Sign the demande de stage document for utilisateur and responsable_de_service role users"""
    
    try:
        user = request.user
        
        # Verify the user has 'utilisateur' or 'responsable_de_service' role
        if user.role not in ['utilisateur', 'responsable_de_service']:
            return Response({
                "error": "Seuls les utilisateurs avec le rôle 'utilisateur' ou 'responsable_de_service' peuvent signer les demandes de stage."
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the stage
        stage = Stage.objects.get(id=stage_id, deleted=False)
        
        # Role-specific validation and signing logic
        if user.role == 'utilisateur':
            # Check if this user is the owner of a sujet in this stage (encadrant)
            if not stage.sujet or stage.sujet.created_by != user:
                return Response({
                    "error": "Vous ne pouvez signer que les stages pour lesquels vous avez créé le sujet."
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if already signed as encadrant
            if stage.is_signed_by_role('encadrant'):
                return Response({
                    "error": "Ce stage a déjà été signé en tant qu'encadrant."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            signature_role = 'encadrant'
            success_message_prefix = "Signature encadrant ajoutée avec succès!"
            
        elif user.role == 'responsable_de_service':
            # Check if already signed as responsable_de_service
            if stage.is_signed_by_role('responsable_de_service'):
                return Response({
                    "error": "Ce stage a déjà été signé en tant que responsable de service."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            signature_role = 'responsable_de_service'
            success_message_prefix = "Signature responsable de service ajoutée avec succès!"
        
        # Check if demande_de_stage exists
        if not stage.demande_de_stage:
            return Response({
                "error": "Aucune demande de stage n'est disponible pour ce stage."
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Load DOCX template (or use the existing demande_de_stage)
            docx_template_path = os.path.join(settings.BASE_DIR, 'resume_service', 'media', 'DEMANDE DE STAGE.docx')
            
            if os.path.exists(docx_template_path):
                # Get current date
                current_date = datetime.now().strftime('%d/%m/%Y')
                
                # Update document data in JSON structure
                stage.update_document_data()
                
                # Prepare replacements dictionary from JSON data and existing signatures
                document_data = stage.demande_de_stage_data.get('document_data', {})
                replacements = {
                    '«NOM»': document_data.get('nom', ''),
                    '«PRENOM»': document_data.get('prenom', ''),
                    '«CIN»': document_data.get('cin', ''),
                    '«TELEPHONE»': document_data.get('telephone', ''),
                    '«SPECIALITE»': document_data.get('specialite', ''),
                    '«ETABLISSEMENT»': document_data.get('etablissement', ''),
                    '«PERIODE_DU»': document_data.get('periode_du', ''),
                    '«PERIODE_AU»': document_data.get('periode_au', ''),
                    '«ENCADRANT»': document_data.get('encadrant', ''),
                    '«SERVICE»': document_data.get('service', ''),
                    '«PERIODE_ACCORDEE_DU»': document_data.get('periode_accordee_du', ''),
                    '«PERIODE_ACCORDEE_AU»': document_data.get('periode_accordee_au', ''),
                    '«SUJET»': document_data.get('sujet', ''),
                    # Initialize signature fields as empty (will be filled based on existing signatures)
                    '«NOM_ENCADRANT»': '',
                    '«DATE_SIGNATURE_ENCADRANT»': '',
                    '«SIGNATURE_ENCADRANT»': '',
                    '«NOM_RESPONSABLE_SERVICE»': '',
                    '«DATE_SIGNATURE_RESPONSABLE_SERVICE»': '',
                    '«SIGNATURE_RESPONSABLE_SERVICE»': '',
                    '«DATE_SIGNATURE_RH»': '',
                    '«SIGNATURE_RH»': ''
                }
                
                # Preserve existing signatures from JSON data
                encadrant_signature = stage.get_signature_info('encadrant')
                if encadrant_signature:
                    replacements['«NOM_ENCADRANT»'] = encadrant_signature['full_name']
                    replacements['«DATE_SIGNATURE_ENCADRANT»'] = encadrant_signature['signed_at']
                    replacements['«SIGNATURE_ENCADRANT»'] = encadrant_signature['full_name']
                
                responsable_service_signature = stage.get_signature_info('responsable_de_service')
                if responsable_service_signature:
                    replacements['«NOM_RESPONSABLE_SERVICE»'] = responsable_service_signature['full_name']
                    replacements['«DATE_SIGNATURE_RESPONSABLE_SERVICE»'] = responsable_service_signature['signed_at']
                    replacements['«SIGNATURE_RESPONSABLE_SERVICE»'] = responsable_service_signature['full_name']
                
                rh_signature = stage.get_signature_info('responsable_rh')
                if rh_signature:
                    replacements['«DATE_SIGNATURE_RH»'] = rh_signature['signed_at']
                    replacements['«SIGNATURE_RH»'] = rh_signature['full_name']
                
                # Apply current user's signature to the appropriate field
                if signature_role == 'encadrant':
                    replacements.update({
                        '«NOM_ENCADRANT»': f"{user.prenom} {user.nom}".title() if user.prenom and user.nom else user.email,
                        '«DATE_SIGNATURE_ENCADRANT»': current_date,
                        '«SIGNATURE_ENCADRANT»': f"{user.prenom} {user.nom}".title() if user.prenom and user.nom else user.email,
                    })
                elif signature_role == 'responsable_de_service':
                    replacements.update({
                        '«NOM_RESPONSABLE_SERVICE»': f"{user.prenom} {user.nom}".title() if user.prenom and user.nom else user.email,
                        '«DATE_SIGNATURE_RESPONSABLE_SERVICE»': current_date,
                        '«SIGNATURE_RESPONSABLE_SERVICE»': f"{user.prenom} {user.nom}".title() if user.prenom and user.nom else user.email,
                    })
                
                # Generate DOCX from template with signature information
                filled_docx_bytes = create_docx_from_template_xml(
                    docx_path=docx_template_path,
                    replacements=replacements
                )
                
                if filled_docx_bytes:
                    # Save signed DOCX to database
                    stage.demande_de_stage = filled_docx_bytes
                    
                    # Convert DOCX to PDF and cache it
                    try:
                        pdf_bytes = convert_docx_bytes_to_pdf_bytes(filled_docx_bytes)
                        if pdf_bytes:
                            stage.demande_de_stage_pdf = pdf_bytes
                    except Exception:
                        pass  # PDF will be generated on-demand
                    
                    # Add signature to JSON structure
                    stage.add_signature(signature_role, user, current_date)
                    
                    # Check if all signatures are present and update stage status
                    if stage.are_all_signatures_complete():
                        stage.statut = 'stage_en_cours'
                        status_message = f"{success_message_prefix} Toutes les signatures sont complètes, le stage est maintenant en cours."
                    else:
                        # Update status to waiting for signatures if not already
                        if stage.statut != 'en_attente_des_signatures':
                            stage.statut = 'en_attente_des_signatures'
                        status_message = f"{success_message_prefix} En attente des autres signatures."
                    
                    stage.save()
                    
                    return Response({
                        "message": status_message,
                        "signer_name": f"{user.prenom} {user.nom}".title() if user.prenom and user.nom else user.username,
                        "signature_date": current_date,
                        "stage_status": stage.statut,
                        "signatures_complete": stage.are_all_signatures_complete()
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "error": "Erreur lors de la génération du document signé."
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    "error": "Template de demande de stage non trouvé."
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as signing_error:
            return Response({
                "error": f"Erreur lors de la signature: {str(signing_error)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Stage.DoesNotExist:
        return Response({
            "error": "Stage non trouvé."
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "error": f"Erreur lors de la signature: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@allow_roles('utilisateur_rh', 'admin_rh')
def sign_demande_stage_rh(request, stage_id):
    """Sign the demande de stage document for RH role users"""
    
    try:
        user = request.user
        
        # Verify the user has RH role
        if user.role not in ['utilisateur_rh', 'admin_rh']:
            return Response({
                "error": "Seuls les utilisateurs avec le rôle RH peuvent signer les demandes de stage."
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the stage
        stage = Stage.objects.get(id=stage_id, deleted=False)
        
        # Check if already signed as responsable_rh
        if stage.is_signed_by_role('responsable_rh'):
            return Response({
                "error": "Ce stage a déjà été signé par les RH."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if demande_de_stage exists
        if not stage.demande_de_stage:
            return Response({
                "error": "Aucune demande de stage n'est disponible pour ce stage."
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Load DOCX template
            docx_template_path = os.path.join(settings.BASE_DIR, 'resume_service', 'media', 'DEMANDE DE STAGE.docx')
            
            if os.path.exists(docx_template_path):
                # Get current date
                current_date = datetime.now().strftime('%d/%m/%Y')
                
                # Update document data in JSON structure
                stage.update_document_data()
                
                # Prepare replacements dictionary from JSON data and existing signatures
                document_data = stage.demande_de_stage_data.get('document_data', {})
                replacements = {
                    '«NOM»': document_data.get('nom', ''),
                    '«PRENOM»': document_data.get('prenom', ''),
                    '«CIN»': document_data.get('cin', ''),
                    '«TELEPHONE»': document_data.get('telephone', ''),
                    '«SPECIALITE»': document_data.get('specialite', ''),
                    '«ETABLISSEMENT»': document_data.get('etablissement', ''),
                    '«PERIODE_DU»': document_data.get('periode_du', ''),
                    '«PERIODE_AU»': document_data.get('periode_au', ''),
                    '«ENCADRANT»': document_data.get('encadrant', ''),
                    '«SERVICE»': document_data.get('service', ''),
                    '«PERIODE_ACCORDEE_DU»': document_data.get('periode_accordee_du', ''),
                    '«PERIODE_ACCORDEE_AU»': document_data.get('periode_accordee_au', ''),
                    '«SUJET»': document_data.get('sujet', ''),
                    # Initialize signature fields as empty (will be filled based on existing signatures)
                    '«NOM_ENCADRANT»': '',
                    '«DATE_SIGNATURE_ENCADRANT»': '',
                    '«SIGNATURE_ENCADRANT»': '',
                    '«NOM_RESPONSABLE_SERVICE»': '',
                    '«DATE_SIGNATURE_RESPONSABLE_SERVICE»': '',
                    '«SIGNATURE_RESPONSABLE_SERVICE»': '',
                    '«DATE_SIGNATURE_RH»': '',
                    '«SIGNATURE_RH»': ''
                }
                
                # Preserve existing signatures from JSON data
                encadrant_signature = stage.get_signature_info('encadrant')
                if encadrant_signature:
                    replacements['«NOM_ENCADRANT»'] = encadrant_signature['full_name']
                    replacements['«DATE_SIGNATURE_ENCADRANT»'] = encadrant_signature['signed_at']
                    replacements['«SIGNATURE_ENCADRANT»'] = encadrant_signature['full_name']
                
                responsable_service_signature = stage.get_signature_info('responsable_de_service')
                if responsable_service_signature:
                    replacements['«NOM_RESPONSABLE_SERVICE»'] = responsable_service_signature['full_name']
                    replacements['«DATE_SIGNATURE_RESPONSABLE_SERVICE»'] = responsable_service_signature['signed_at']
                    replacements['«SIGNATURE_RESPONSABLE_SERVICE»'] = responsable_service_signature['full_name']
                
                # Apply current RH user's signature
                replacements.update({
                    '«DATE_SIGNATURE_RH»': current_date,
                    '«SIGNATURE_RH»': f"{user.prenom} {user.nom}".title() if user.prenom and user.nom else user.email,
                })
                
                # Generate DOCX from template with RH signature information
                filled_docx_bytes = create_docx_from_template_xml(
                    docx_path=docx_template_path,
                    replacements=replacements
                )
                
                if filled_docx_bytes:
                    # Save signed DOCX to database
                    stage.demande_de_stage = filled_docx_bytes
                    
                    # Convert DOCX to PDF and cache it
                    try:
                        pdf_bytes = convert_docx_bytes_to_pdf_bytes(filled_docx_bytes)
                        if pdf_bytes:
                            stage.demande_de_stage_pdf = pdf_bytes
                    except Exception:
                        pass  # PDF will be generated on-demand
                    
                    # Add signature to JSON structure
                    stage.add_signature('responsable_rh', user, current_date)
                    
                    # Check if all signatures are present and update stage status
                    if stage.are_all_signatures_complete():
                        stage.statut = 'stage_en_cours'
                        status_message = "Signature RH ajoutée avec succès! Toutes les signatures sont complètes, le stage est maintenant en cours."
                    else:
                        # Update status to waiting for signatures if not already
                        if stage.statut != 'en_attente_des_signatures':
                            stage.statut = 'en_attente_des_signatures'
                        status_message = "Signature RH ajoutée avec succès! En attente des autres signatures."
                    
                    stage.save()
                    
                    return Response({
                        "message": status_message,
                        "signer_name": f"{user.prenom} {user.nom}".title() if user.prenom and user.nom else user.username,
                        "signature_date": current_date,
                        "stage_status": stage.statut,
                        "signatures_complete": stage.are_all_signatures_complete()
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "error": "Erreur lors de la génération du document signé."
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({
                    "error": "Template de demande de stage non trouvé."
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as signing_error:
            return Response({
                "error": f"Erreur lors de la signature: {str(signing_error)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Stage.DoesNotExist:
        return Response({
            "error": "Stage non trouvé."
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "error": f"Erreur lors de la signature: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@allow_roles('admin')  # Only admin can sign as chef de département
def sign_demande_stage_chef_dept(request, stage_id):
    """Sign the demande de stage document for Chef de Département role users"""
    
    try:
        user = request.user
        
        # Verify the user has admin role (chef de département)
        if user.role != 'admin':
            return Response({
                "error": "Seuls les utilisateurs avec le rôle admin peuvent signer en tant que chef de département."
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get the stage
        stage = Stage.objects.get(id=stage_id, deleted=False)
        
        # Check if demande_de_stage exists
        if not stage.demande_de_stage:
            return Response({
                "error": "Aucune demande de stage n'est disponible pour ce stage."
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Load DOCX template
            docx_template_path = os.path.join(settings.BASE_DIR, 'resume_service', 'media', 'DEMANDE DE STAGE.docx')
            
            if os.path.exists(docx_template_path):
                # Get current date
                current_date = datetime.now().strftime('%d/%m/%Y')
                
                # Prepare replacements dictionary
                replacements = {
                    '«NOM»': stage.stagiaire.nom.upper() if stage.stagiaire.nom else '',
                    '«PRENOM»': stage.stagiaire.prenom.title() if stage.stagiaire.prenom else '',
                    '«CIN»': stage.stagiaire.matricule if stage.stagiaire.matricule else '',
                    '«EMAIL»': stage.stagiaire.email if stage.stagiaire.email else '',
                    '«TELEPHONE»': stage.stagiaire.num_tel if stage.stagiaire.num_tel else '',
                    '«DATE_NAISSANCE»': stage.stagiaire.date_naissance.strftime('%d/%m/%Y') if stage.stagiaire.date_naissance else '',
                    '«NATURE»': stage.nature.upper() if stage.nature else '',
                    '«DATE_DEBUT»': stage.date_debut.strftime('%d/%m/%Y') if stage.date_debut else '',
                    '«DATE_FIN»': stage.date_fin.strftime('%d/%m/%Y') if stage.date_fin else '',
                    '«PERIODE_DU»': stage.date_debut.strftime('%d/%m/%Y') if stage.date_debut else '',
                    '«PERIODE_AU»': stage.date_fin.strftime('%d/%m/%Y') if stage.date_fin else '',
                    '«PERIODE_ACCORDEE_DU»': stage.date_debut.strftime('%d/%m/%Y') if stage.date_debut else '',
                    '«PERIODE_ACCORDEE_AU»': stage.date_fin.strftime('%d/%m/%Y') if stage.date_fin else '',
                    '«SUJET»': stage.sujet.titre if stage.sujet and stage.sujet.titre else '',
                    '«DESCRIPTION_SUJET»': stage.sujet.description if stage.sujet and stage.sujet.description else '',
                    '«DATE_DEMANDE»': current_date,
                    '«SPECIALITE»': '',
                    '«ETABLISSEMENT»': '',
                    '«DIRECTION»': '',
                    '«ENCADRANT»': '',
                    '«SERVICE»': '',
                    # Preserve existing signatures
                    '«NOM_ENCADRANT»': '',
                    '«DATE_SIGNATURE_ENCADRANT»': '',
                    '«SIGNATURE_ENCADRANT»': '',
                    # Chef de département signature fields - but don't set as Responsable du service yet
                    '«NOM_RESPONSABLE_SERVICE»': '',
                    '«DATE_SIGNATURE_RESPONSABLE_SERVICE»': '',
                    '«SIGNATURE_RESPONSABLE_SERVICE»': '',
                    # RH signature fields
                    '«DATE_SIGNATURE_RH»': '',
                    '«SIGNATURE_RH»': '',
                }
                
                # Preserve existing signatures from JSON data
                encadrant_signature = stage.get_signature_info('encadrant')
                if encadrant_signature:
                    # Encadrant should always be the "Responsable du service"
                    replacements['«NOM_RESPONSABLE_SERVICE»'] = encadrant_signature['full_name']
                    replacements['«DATE_SIGNATURE_RESPONSABLE_SERVICE»'] = encadrant_signature['signed_at']
                    replacements['«SIGNATURE_RESPONSABLE_SERVICE»'] = encadrant_signature['full_name']
                    # Also fill the encadrant-specific fields
                    replacements['«NOM_ENCADRANT»'] = encadrant_signature['full_name']
                    replacements['«DATE_SIGNATURE_ENCADRANT»'] = encadrant_signature['signed_at']
                    replacements['«SIGNATURE_ENCADRANT»'] = encadrant_signature['full_name']
                
                rh_signature = stage.get_signature_info('responsable_rh')
                if rh_signature:
                    replacements['«DATE_SIGNATURE_RH»'] = rh_signature['signed_at']
                    replacements['«SIGNATURE_RH»'] = rh_signature['full_name']
                
                # Generate DOCX
                filled_docx_bytes = create_docx_from_template_xml(
                    docx_path=docx_template_path,
                    replacements=replacements
                )
                
                if filled_docx_bytes:
                    stage.demande_de_stage = filled_docx_bytes
                    
                    # Convert DOCX to PDF and cache it
                    try:
                        pdf_bytes = convert_docx_bytes_to_pdf_bytes(filled_docx_bytes)
                        if pdf_bytes:
                            stage.demande_de_stage_pdf = pdf_bytes
                    except Exception:
                        pass  # PDF will be generated on-demand
                    
                    # Add signature to JSON structure
                    stage.add_signature('chef_departement', user, current_date)
                    
                    # Check all signatures
                    if stage.are_all_signatures_complete():
                        stage.statut = 'stage_en_cours'
                        status_message = "Toutes les signatures sont complètes, le stage est maintenant en cours."
                    else:
                        if stage.statut != 'en_attente_des_signatures':
                            stage.statut = 'en_attente_des_signatures'
                        status_message = "Signature chef de département ajoutée. En attente des autres signatures."
                    
                    stage.save()
                    
                    return Response({
                        "message": status_message,
                        "signer_name": f"{user.prenom} {user.nom}".title() if user.prenom and user.nom else user.username,
                        "signature_date": current_date,
                        "stage_status": stage.statut,
                        "signatures_complete": stage.are_all_signatures_complete()
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Erreur lors de la génération du document signé."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"error": "Template de demande de stage non trouvé."}, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as signing_error:
            return Response({"error": f"Erreur lors de la signature: {str(signing_error)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Stage.DoesNotExist:
        return Response({"error": "Stage non trouvé."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Erreur lors de la signature: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)