from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import status



@csrf_exempt
@api_view(['POST'])  # ← ✅ This is the annotation you meant
def upload_pdf(request):
    pdf_file = request.FILES['file']
    pdf_bytes = pdf_file.read()
    return Response({"message": "PDF received", "size": len(pdf_bytes)})

@csrf_exempt
@api_view(['POST', 'GET', 'PUT', 'DELETE', 'PATCH'])
def test(request):
    return Response({'message': 'Test endpoint is working'}, status=status.HTTP_200_OK)