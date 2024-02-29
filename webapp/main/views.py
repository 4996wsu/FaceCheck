from django.shortcuts import render, redirect

from database import update_student_photo
from preprocess import detect_and_crop_face, face_encode, make_pt_file

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
from django.contrib import messages

def upload_image_to_firebase(file):
    # Create a Firebase Storage reference
    bucket = storage.bucket()

    blob = bucket.blob( file.name)
    blob.upload_from_string(
        file.read(),
        content_type=file.content_type
    )
    blob.make_public()
    return blob.public_url

def delete_file_from_firebase(file_name):
    bucket = storage.bucket()
    blob = bucket.blob(file_name)
    blob.delete()


def enroll(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            image_url = upload_image_to_firebase(image)
            name = request.user.username
            
            result = update_student_photo(name, image_url)
            delete_file_from_firebase(image.name)
            # Success message and error handling        
            
            if result == None:
                messages.warning(request, 'Photo is invalid. Please upload a photo with one face in it.')
            else:
                messages.warning(request, 'Successfully uploaded photo.')
            
            return render(request, 'main/enrollment.html', {'form': form})

        else:
            return HttpResponse("Invalid form.")
    else:
        form = ImageUploadForm()
    return render(request, 'main/enrollment.html', {'form': form})
