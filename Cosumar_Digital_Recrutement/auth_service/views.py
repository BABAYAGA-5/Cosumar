
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

def get_private_key():
    try:
        with open(settings.BASE_DIR / 'keys' / 'private.pem') as f:
            return f.read()
    except FileNotFoundError:
        return settings.SECRET_KEY

def get_public_key():
    try:
        with open(settings.BASE_DIR / 'keys' / 'public.pem') as f:
            return f.read()
    except FileNotFoundError:
        return settings.SECRET_KEY

@csrf_exempt
@api_view(['POST', 'GET', 'PUT', 'DELETE', 'PATCH'])
def test(request):
   return Response({'message': 'Test endpoint is working'}, status=status.HTTP_200_OK)

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
        
        if user.mot_de_passe == mot_de_passe:
            payload = {
                'user_id': user.id,
                'email': user.email,
                'role': user.get_role_display() if hasattr(user, 'get_role_display') else user.role,
                "auth": True
            }
            
            private_key = get_private_key()
            # Use HS256 algorithm since we're using SECRET_KEY as fallback
            algorithm = 'RS256' if 'BEGIN PRIVATE KEY' in private_key else 'HS256'
            token = jwt.encode(payload, private_key, algorithm=algorithm)
            
            return Response({'token': token, 'user': payload}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Identifiants invalides',
                             'email': request.data.get("email"),
                             'mot_de_passe':request.data.get("mot_de_passe"),
                             'pass':user.mot_de_passe,
                             'mail':user.email}, status=status.HTTP_401_UNAUTHORIZED)
            
    except Utilisateur.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Log the actual error for debugging
        print(f"Login error: {str(e)}")
        return Response({'error': 'Erreur interne du serveur'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def decode_jwt(token):
    try:
        verification_key = get_public_key()
        algorithm = 'RS256' if 'BEGIN PUBLIC KEY' in verification_key else 'HS256'
        return jwt.decode(token, verification_key, algorithms=[algorithm])
    except Exception as e:
        print(f"JWT decode error: {str(e)}")
        raise

@csrf_exempt
@api_view(['POST'])
def jwtcheck(request):
    try:
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)

        payload = decode_jwt(token)
        return Response({'payload': payload}, status=status.HTTP_200_OK)
        
    except jwt.ExpiredSignatureError:
        return Response({'error': 'Token has expired'}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        print(f"JWT check error: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
def signup(request):
    try:
        prenom = request.data.get('prenom')
        nom = request.data.get('nom')
        email = request.data.get('email')
        mot_de_passe = request.data.get('mot_de_passe')
        confirmer_mot_de_passe = request.data.get('confirmer_mot_de_passe')
        
        if not email or not mot_de_passe:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user already exists
        if Utilisateur.objects.filter(email=email).exists():
            return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)

        if mot_de_passe != confirmer_mot_de_passe:
            return Response({'error': 'Passwords do not match',
                             'mot_de_passe': mot_de_passe,
                             'confirmer_mot_de_passe':confirmer_mot_de_passe}, status=status.HTTP_400_BAD_REQUEST)

        # Create new user
        mot_de_passe = hashlib.sha256(mot_de_passe.encode()).hexdigest()
        user = Utilisateur(email=email, mot_de_passe=mot_de_passe)
        if prenom:
            user.prenom = prenom
        if nom:
            user.nom = nom
        user.save()
        
        return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"Signup error: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)