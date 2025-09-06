
import datetime
import uuid
from django.shortcuts import render
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from resume_service.models import Logs
from .models import Utilisateur
import jwt
from django.conf import settings
import hashlib
import random
import string
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
import os
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

def get_private_key():
    try:
        with open(settings.BASE_DIR / 'keys' / 'private.pem') as f:
            return f.read()
    except FileNotFoundError:
        return settings.SECRET_KEY



@csrf_exempt
@api_view(['POST'])
def login(request):
    try:
        email = request.data.get('email')
        mot_de_passe = request.data.get('mot_de_passe')
        
        if not email or not mot_de_passe:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Hash the password
        mot_de_passe = hashlib.sha256(mot_de_passe.encode()).hexdigest()

        # Check if user exists
        user = Utilisateur.objects.get(email=email)
        
        if user.is_active == False:
            return Response({'error': 'Utilisateur inactif'}, status=status.HTTP_403_FORBIDDEN)

        if user.mot_de_passe == mot_de_passe:
            refresh = RefreshToken.for_user(user)

            access_token = refresh.access_token
            access_token['email'] = user.email
            access_token['role'] = user.role

            return Response({
                'refresh': str(refresh), 
                'access': str(access_token),
                'user': {
                'user_id': user.id,
                'prenom': user.prenom,
                'nom': user.nom,
                'email': user.email,
                'role': user.role,
            }}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Identifiants invalides'}, status=status.HTTP_401_UNAUTHORIZED)
            
    except Utilisateur.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Log the actual error for debugging
        print(f"Login error: {str(e)}")
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@csrf_exempt
@api_view(['POST'])
def signup(request):
    try:
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return Response({'error': 'Token missing or invalid'}, status=401)

        jwt_token = auth_header.split(' ')[1]
        print(f"Received JWT token: {jwt_token}")   
        prenom = request.data.get('prenom')
        nom = request.data.get('nom')
        email = request.data.get('email')
        
        if not email:
            return Response({'error': 'Email est requis'}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(email, str) or '@' not in email or '.' not in email:
            return Response({'error': 'Email invalide'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user already exists
        if Utilisateur.objects.filter(email=email).exists():
            return Response({'error': 'L\'utilisateur existe déjà'}, status=status.HTTP_400_BAD_REQUEST)

        mot_de_passe = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
        
        send_mail(
                subject="Bienvenue sur Cosumar Digital Recrutement",
                message=f"Bonjour {prenom},\n\nVotre compte a été créé avec succès. Votre mot de passe est : {mot_de_passe} .\n\n Veuillez le changer après votre première connexion. \n\nMerci.",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )

        mot_de_passe = hashlib.sha256(mot_de_passe.encode()).hexdigest()
        user = Utilisateur(email=email, mot_de_passe=mot_de_passe)
        if prenom:
            user.prenom = prenom
        if nom:
            user.nom = nom
        user.save()

        # Log the signup action
        Logs.objects.create(action=f"Creation d'utilisateur id {user.id}", utilisateur=user)

        return Response({'message': 'Utilisateur créé avec succès'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"Signup error: {str(e)}")
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@csrf_exempt
@api_view(['POST', 'GET'])
def test(request):
    return Response({'message': 'Test API call successful'}, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['GET'])
def get_all_utilisateurs(request):
    """Get paginated utilisateurs for admin/admin_rh users with filtering support"""
    try:
        # Get pagination parameters
        page_number = request.GET.get('page', 1)
        page_size = int(request.GET.get('page_size', 25))
        
        # Get filter parameters
        search = request.GET.get('search', '').strip()
        role_filter = request.GET.get('role', '').strip()
        departement_filter = request.GET.get('departement', '').strip()
        is_active_filter = request.GET.get('is_active', '').strip()
        
        # Start with all utilisateurs
        utilisateurs_queryset = Utilisateur.objects.all()
        
        # Apply filters
        if search:
            # Search in nom, prenom, and email fields
            utilisateurs_queryset = utilisateurs_queryset.filter(
                Q(nom__icontains=search) | 
                Q(prenom__icontains=search) | 
                Q(email__icontains=search)
            )
        
        if role_filter:
            utilisateurs_queryset = utilisateurs_queryset.filter(role=role_filter)
        
        if departement_filter:
            utilisateurs_queryset = utilisateurs_queryset.filter(departement=departement_filter)
        
        if is_active_filter:
            # Convert string to boolean
            is_active_bool = is_active_filter.lower() == 'true'
            utilisateurs_queryset = utilisateurs_queryset.filter(is_active=is_active_bool)
        
        # Order by creation date (newest first)
        utilisateurs_queryset = utilisateurs_queryset.order_by('-date_creation')
        
        # Create paginator
        paginator = Paginator(utilisateurs_queryset, page_size)
        
        try:
            utilisateurs_page = paginator.page(page_number)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            utilisateurs_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page
            utilisateurs_page = paginator.page(paginator.num_pages)
        
        # Build response data
        utilisateurs_data = []
        for user in utilisateurs_page:
            utilisateurs_data.append({
                'id': user.id,
                'nom': user.nom,
                'prenom': user.prenom,
                'email': user.email,
                'role': user.role,
                'departement': user.departement,
                'is_active': user.is_active,
                'created_at': user.date_creation,
                'updated_at': user.date_creation  # Using date_creation since there's no updated field
            })
        
        # Return paginated response with filter info
        return Response({
            'results': utilisateurs_data,
            'count': paginator.count,
            'page': utilisateurs_page.number,
            'page_size': page_size,
            'total_pages': paginator.num_pages,
            'has_next': utilisateurs_page.has_next(),
            'has_previous': utilisateurs_page.has_previous(),
            'next_page_number': utilisateurs_page.next_page_number() if utilisateurs_page.has_next() else None,
            'previous_page_number': utilisateurs_page.previous_page_number() if utilisateurs_page.has_previous() else None,
            'filters': {
                'search': search,
                'role': role_filter,
                'departement': departement_filter,
                'is_active': is_active_filter
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Get utilisateurs error: {str(e)}")
        return Response({'error': 'Erreur lors de la récupération des utilisateurs'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['GET'])
def get_user_profile(request, user_id):
    """Get user profile by ID for authenticated users"""
    try:
        # Get user by ID
        user = Utilisateur.objects.get(id=user_id)
        
        # Build response data
        user_data = {
            'id': user.id,
            'nom': user.nom,
            'prenom': user.prenom,
            'email': user.email,
            'departement': user.departement,
            'role': user.role,
            'is_active': user.is_active,
            'date_joined': user.date_creation
        }
        
        return Response(user_data, status=status.HTTP_200_OK)
        
    except Utilisateur.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Get user profile error: {str(e)}")
        return Response({'error': 'Erreur lors de la récupération du profil'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['PATCH'])
def update_user_role(request, user_id):
    """Update user role - only admins can do this and cannot demote other admins"""
    try:
    
        # Get the user to update
        user_to_update = Utilisateur.objects.get(id=user_id)
        
        # Check if trying to demote an admin
        if user_to_update.role == 'admin':
            return Response({'error': 'Impossible de modifier le rôle d\'un administrateur'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get the new role from request
        new_role = request.data.get('role')
        if not new_role:
            return Response({'error': 'Le nouveau rôle est requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate the new role
        valid_roles = ['admin_rh', 'utilisateur_rh', 'utilisateur']
        if new_role not in valid_roles:
            return Response({'error': f'Rôle invalide. Rôles valides: {", ".join(valid_roles)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update the user's role
        old_role = user_to_update.role
        user_to_update.role = new_role
        user_to_update.save()
        
        # Log the action
        Logs.objects.create(
            action=f"Changement de rôle utilisateur {user_to_update.id} de '{old_role}' vers '{new_role}'",
            utilisateur=user_to_update
        )
        
        return Response({
            'message': 'Rôle mis à jour avec succès',
            'user_id': user_id,
            'old_role': old_role,
            'new_role': new_role
        }, status=status.HTTP_200_OK)
        
    except Utilisateur.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Update user role error: {str(e)}")
        return Response({'error': 'Erreur lors de la mise à jour du rôle'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_user_activity(request, user_id):
    """Activate or deactivate a user account - only admins can do this and cannot deactivate other admins"""
    try:
        # Get the user to update
        user_to_update = Utilisateur.objects.get(id=user_id)
        
        # Check if trying to deactivate an admin
        if user_to_update.role == 'admin':
            return Response({'error': 'Impossible de modifier le statut d\'un administrateur'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get the new activity status from request
        is_active = request.data.get('is_active')
        if is_active is None:
            return Response({'error': 'Le statut actif est requis'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(is_active, bool):
            return Response({'error': 'Le statut actif doit être un booléen'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update the user's activity status
        old_status = user_to_update.is_active
        user_to_update.is_active = is_active
        user_to_update.save()
        
        # Log the action
        Logs.objects.create(
            action=f"Changement de statut utilisateur {user_to_update.id} de '{old_status}' vers '{is_active}'",
            utilisateur=user_to_update
        )
        
        return Response({
            'message': 'Statut mis à jour avec succès',
            'user_id': user_id,
            'old_status': old_status,
            'new_status': is_active
        }, status=status.HTTP_200_OK)
        
    except Utilisateur.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Update user activity error: {str(e)}")
        return Response({'error': 'Erreur lors de la mise à jour du statut'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)