
import datetime
import uuid
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Utilisateur
import jwt
from django.conf import settings
import hashlib
import random
import string
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
import os

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

        return Response({'message': 'Utilisateur créé avec succès'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"Signup error: {str(e)}")
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@csrf_exempt
@api_view(['POST', 'GET'])
def test(request):
    return Response({'message': 'Test API call successful'}, status=status.HTTP_200_OK)