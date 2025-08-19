from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import FileUploadParser
from django.shortcuts import render
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import status
import os
import filetype

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

from resume_service.models import Stage, Stagiaire, Sujet
from auth_service.models import Utilisateur
from django.db.models import Count, Q
from datetime import datetime, timedelta

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
    """Save user with CIN data and file"""
    try:
        nom = request.data.get('nom')
        prenom = request.data.get('prenom')
        cin = request.data.get('cin')
        date_naissance = request.data.get('date_naissance')
        status_stage = request.data.get('status', 'stage_created')
        candidate_method = request.data.get('candidate_method', 'new')
        
        # New stage fields
        nature = request.data.get('nature')
        date_debut = request.data.get('date_debut')
        date_fin = request.data.get('date_fin')
        sujet_id = request.data.get('sujet_id')
        
        cin_file = request.FILES.get('cin_file')
        cv_file = request.FILES.get('cv_file')
        assurance_file = request.FILES.get('assurance_file')
        convention_file = request.FILES.get('convention_file')
        lettre_motivation_file = request.FILES.get('lettre_motivation_file')

        # Validation based on candidate method
        if candidate_method == 'new':
            if not all([nom, prenom, cin, cin_file, cv_file, nature, date_debut, date_fin]):
                return Response({
                    "error": "Pour un nouveau candidat: Nom, prénom, numéro CIN, fichier CIN, CV et informations de stage sont requis."
                }, status=status.HTTP_400_BAD_REQUEST)
        else:  # existing candidate
            if not all([nom, prenom, cin, cv_file, nature, date_debut, date_fin]):
                return Response({
                    "error": "Pour un candidat existant: Nom, prénom, numéro CIN, CV et informations de stage sont requis."
                }, status=status.HTTP_400_BAD_REQUEST)

        # Determine stage status based on available documents
        if assurance_file and convention_file:
            statut_stage = 'en_attente_visite_medicale'
        else:
            statut_stage = 'en_attente_depot_dossier'

        cin_bytes = None
        if cin_file:
            cin_bytes = cin_file.read()

        parsed_date = None
        if date_naissance:
            try:
                parsed_date = datetime.strptime(date_naissance, "%Y-%m-%d").date()
            except ValueError:
                return Response({
                    "error": "Format de date invalide. Utilisez YYYY-MM-DD."
                }, status=status.HTTP_400_BAD_REQUEST)

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
            
        # Check if stagiaire exists, create if not (and method is 'new')
        stagiaire = Stagiaire.objects.filter(matricule=cin).first()
        if not stagiaire and candidate_method == 'new':
            stagiaire = Stagiaire.objects.create(
                nom=nom,
                prenom=prenom,
                matricule=cin,
                date_naissance=parsed_date,
                cin=cin_bytes
            )
            stagiaire.save()
        elif not stagiaire and candidate_method == 'existing':
            return Response({
                "error": "Candidat existant non trouvé."
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

        # Always create a new stage for this stagiaire
        stage = Stage.objects.create(
            stagiaire=stagiaire,
            nature=nature,
            date_debut=parsed_date_debut,
            date_fin=parsed_date_fin,
            sujet=sujet,  # Add sujet to stage creation
            cv=cv_file.read() if cv_file else None,
            convention=convention_file.read() if convention_file else None,
            assurance=assurance_file.read() if assurance_file else None,
            lettre_motivation=lettre_motivation_file.read() if lettre_motivation_file else None,
            statut=statut_stage
        )

        stage.save()

        # Determine success message based on status
        if status_stage == 'dossier_complete':
            message = "Dossier de stage complété avec succès!"
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
            "error": f"Erreur lors de l'enregistrement: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chercher_stagiaires(request):
    """Search for existing stagiaires"""
    try:
        search_query = request.GET.get('search', '').strip()
        
        # Search in nom, prenom, matricule fields and concatenated "prenom nom"
        from django.db.models import Value, CharField
        from django.db.models.functions import Concat
        
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
        ).order_by('nom', 'prenom')[:10]
        
        return Response(list(stagiaires), status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": f"Erreur lors de la recherche des stagiaires: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chercher_sujets(request):
    """Search for existing sujets"""
    try:
        search_query = request.GET.get('search', '').strip()
        
        if len(search_query) < 2:
            return Response([], status=status.HTTP_200_OK)
        
        # Search in titre and description fields
        sujets = Sujet.objects.filter(
            deleted=False
        ).filter(
            Q(titre__icontains=search_query) |
            Q(description__icontains=search_query)
        ).values(
            'id', 'titre', 'description'
        ).order_by('titre')[:10]  # Limit to 10 results
        
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

        if (nature and stagiaire_nom and stagiaire_prenom and date_debut and date_fin and statut and sujet_titre and created_at) is None:
            stages = Stage.objects.filter(deleted=False).values(
                'id', 'nature', 'stagiaire__nom', 'stagiaire__prenom', 'date_debut', 'date_fin', 'statut', 'sujet__titre', 'created_at'
            ).order_by('created_at')

            return Response(list(stages), status=status.HTTP_200_OK)
        else:
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

            stages = (
                Stage.objects.filter(**filters)
                .values(
                    'id',
                    'nature',
                    'stagiaire__nom',
                    'stagiaire__prenom',
                    'date_debut',
                    'date_fin',
                    'statut',
                    'sujet__titre',
                    'created_at'
                )
                .order_by('created_at')
            )

        return Response(list(stages), status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            "error": f"Erreur lors de la recherche des stages: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
