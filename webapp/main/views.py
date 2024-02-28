from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render
from django.http import JsonResponse
import firebase_admin
from firebase_admin import credentials, storage
import os
from pathlib import Path
import tempfile
from django.shortcuts import render, redirect
from .forms import ImageUploadForm
from django.http import HttpResponse
# Create your views here.
def home(request):
    return render(request, 'main/home.html')

def stats(request):
    return render(request, 'main/stats.html')

def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/home')
    else: 
        form = RegisterForm()
    
    return render(request, 'registration/sign_up.html', {"form": form})
if not firebase_admin._apps:
    cred_fp = str(Path.cwd()) + "\db_credentials.json"
    cred = credentials.Certificate(cred_fp)
    firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})
from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def upload_image_to_firebase(file):
    # Create a Firebase Storage reference
    bucket = storage.bucket()
    blob = bucket.blob( file.name)
    blob.upload_from_string(
        file.read(),
        content_type=file.content_type
    )
    return blob.public_url

def enroll(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            image_url = upload_image_to_firebase(image)
            return HttpResponse(f"Image Uploaded Successfully. URL: {image_url}")
        else:
            return HttpResponse("Invalid form.")
    else:
        form = ImageUploadForm()
    return render(request, 'main/enrollment.html', {'form': form})
