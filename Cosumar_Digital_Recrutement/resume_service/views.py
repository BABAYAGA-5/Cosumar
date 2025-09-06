from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FileUploadParser
from django.shortcuts import render
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os
import filetype
from .PDF import extract_cv_data, create_pdf_from_docx_template_xml, create_docx_from_template_xml, convert_docx_bytes_to_pdf_bytes
from resume_service.models import Stage, Stagiaire, Sujet
from auth_service.models import Utilisateur
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.db.models import Value, CharField
from django.db.models.functions import Concat

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
def enregistrer_stagiaire(request):
    """Save new stagiaire with CIN data only (without creating stage)"""
    try:
        nom = request.data.get('nom')
        prenom = request.data.get('prenom')
        cin = request.data.get('cin')
        date_naissance = request.data.get('date_naissance')
        email = request.data.get('email')
        phone = request.data.get('phone')
        
        # Required files for new stagiaire
        cin_file = request.FILES.get('cin_file')

        # Validation for new candidate only
        if not all([nom, prenom, cin, cin_file, email, phone]):
            return Response({
                "error": "Nom, prénom, numéro CIN, fichier CIN, email et téléphone sont requis."
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
            num_tel=phone
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

        # Check if stagiaire exists
        stagiaire = Stagiaire.objects.filter(matricule=matricule, deleted=False).first()
        if not stagiaire:
            return Response({
                "error": "Stagiaire non trouvé. Vous devez d'abord créer le stagiaire."
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
        if sujet_id:
            try:
                sujet = Sujet.objects.get(id=sujet_id, deleted=False)
            except Sujet.DoesNotExist:
                return Response({
                    "error": "Sujet sélectionné non trouvé."
                }, status=status.HTTP_400_BAD_REQUEST)

        # Create new stage for the stagiaire
        stage = Stage.objects.create(
            stagiaire=stagiaire,
            nature=nature,
            date_debut=parsed_date_debut,
            date_fin=parsed_date_fin,
            sujet=sujet,
            cv=cv_file.read() if cv_file else None,
            convention=convention_file.read() if convention_file else None,
            assurance=assurance_file.read() if assurance_file else None,
            lettre_motivation=lettre_motivation_file.read() if lettre_motivation_file else None,
            statut=statut_stage
        )

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
                    '«NOM_RESPONSABLE_SERVICE»': '',
                    '«DATE_SIGNATURE_RESPONSABLE_SERVICE»': '',
                    '«DATE_SIGNATURE_RH»': ''
                }
                
                # Debug: Print all replacements
                print(f"🔍 Debug: Replacements dictionary:")
                for key, value in replacements.items():
                    print(f"  {key} -> {value}")
                
                # Define output path for debugging
                debug_filename = f"{stage.stagiaire.matricule}_demande_stage_{stage.id}.docx"
                debug_path = os.path.join(settings.BASE_DIR, 'resume_service', 'media', debug_filename)
                
                # Generate DOCX from template using XML method
                filled_docx_bytes = create_docx_from_template_xml(
                    docx_path=docx_template_path,
                    replacements=replacements
                )
                
                if filled_docx_bytes:
                    # Save DOCX to database
                    stage.demande_de_stage = filled_docx_bytes
                    stage.save()
                    
                    # Save debug copy as DOCX
                    with open(debug_path, 'wb') as debug_file:
                        debug_file.write(filled_docx_bytes)
                    
                    print(f"✅ DOCX demande de stage generated successfully for matricule: {stage.stagiaire.matricule}")
                    print(f"📁 Debug copy saved at: {debug_path}")
                else:
                    print(f"❌ Failed to generate DOCX from template")
                    
            else:
                print(f"⚠️ Template DOCX not found at: {docx_template_path}")
                
        except Exception as pdf_error:
            print(f"❌ Error generating PDF demande de stage: {str(pdf_error)}")
            # Don't fail the stage creation if PDF generation fails

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
        
        
        stagiaires = Stagiaire.objects.filter(
            deleted=False
        ).annotate(
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
        ).order_by('titre')[:10]  # Limit to 10 results

        print(list(sujets))

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

        # Get stages with all related data
        stages_queryset = Stage.objects.filter(**filters).select_related('stagiaire', 'sujet').order_by('-created_at')
        
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
                } if stage.sujet else None
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
            } if stage.sujet else None
        }

        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
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
        print(f"🔍 Debug: Requesting document - stage_id: {stage_id}, document_type: {document_type}")
        
        stage = Stage.objects.filter(id=stage_id, deleted=False).first()
        
        if not stage:
            print(f"❌ Debug: Stage {stage_id} not found or deleted")
            return Response(
                {"error": "Stage not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        print(f"✅ Debug: Stage {stage_id} found")
        print(f"🔍 Debug: Stage has demande_de_stage: {stage.demande_de_stage is not None}")
        if stage.demande_de_stage:
            print(f"🔍 Debug: demande_de_stage size: {len(stage.demande_de_stage)} bytes")
            
        document_data = None
        content_type = 'application/pdf'
        filename_prefix = document_type
        
        if document_type == 'cv' and stage.cv:
            document_data = stage.cv
            print(f"✅ Debug: Found CV document")
        elif document_type == 'convention' and stage.convention:
            document_data = stage.convention
            print(f"✅ Debug: Found convention document")
        elif document_type == 'assurance' and stage.assurance:
            document_data = stage.assurance
            print(f"✅ Debug: Found assurance document")
        elif document_type == 'lettre_motivation' and stage.lettre_motivation:
            document_data = stage.lettre_motivation
            print(f"✅ Debug: Found lettre_motivation document")
        elif document_type == 'demande_de_stage' and stage.demande_de_stage:
            print(f"🔄 Debug: Converting DOCX to PDF for demande_de_stage")
            # Convert stored DOCX to PDF for serving
            pdf_data = convert_docx_bytes_to_pdf_bytes(stage.demande_de_stage)
            if pdf_data:
                document_data = pdf_data
                print(f"✅ Debug: Successfully converted DOCX to PDF, size: {len(pdf_data)} bytes")
            else:
                print(f"❌ Debug: Failed to convert DOCX to PDF")
                return Response(
                    {"error": "Failed to convert demande de stage to PDF"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            print(f"❌ Debug: Document '{document_type}' not found or empty")
            print(f"🔍 Debug: Available documents - cv: {stage.cv is not None}, convention: {stage.convention is not None}, assurance: {stage.assurance is not None}, lettre_motivation: {stage.lettre_motivation is not None}, demande_de_stage: {stage.demande_de_stage is not None}")
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
    """Get paginated stagiaires for admin/admin_rh users"""
    try:
        # Get pagination parameters
        page_number = request.GET.get('page', 1)
        page_size = int(request.GET.get('page_size', 25))
        
        # Get all non-deleted stagiaires ordered by creation date
        stagiaires_queryset = Stagiaire.objects.filter(deleted=False).order_by('date_creation')
        
        # Create paginator
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
        print(f"Get stagiaires error: {str(e)}")
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