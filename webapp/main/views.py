from django.shortcuts import render, redirect


from database import update_student_photo
from preprocess import detect_and_crop_face, face_encode, make_pt_file
from django.contrib.auth.forms import PasswordResetForm
from .forms import RegisterForm, ProfileForm
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
import firebase_admin
from firebase_admin import auth
from .forms import RegisterForm
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponse
import random
from datetime import datetime
from django.core.mail import send_mail
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.auth.models import User
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib import messages

# Create your views here.
def home(request):
    return render(request, 'main/home.html')

def stats(request):
    return render(request, 'main/stats.html')
def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        if form.is_valid() and profile_form.is_valid():
            user = form.save(commit=False)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, 'Account created successfully. Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid form submission.')
    else:
        form = RegisterForm()
        profile_form = ProfileForm()

    return render(request, 'registration/sign_up.html', {'form': form, 'profile_form': profile_form})

def otp_verification(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        otp_time_str = request.session.get('otp_time')
        if otp_time_str:
            otp_time = datetime.strptime(otp_time_str, '%Y-%m-%d %H:%M:%S.%f')
            if datetime.now() - otp_time > timedelta(minutes=2):  # Check if more than 2 minutes have passed
                messages.error(request, 'OTP expired. Please sign up again.')
                # Redirect to the signup page
                return redirect('signup')
            elif otp == str(request.session.get('otp')):
                try:
                    User.objects.create_user(
                        username=request.session.get('username'),
                        email=request.session.get('email'),
                        password=request.session.get('password')
                    )
                    messages.success(request, 'User created successfully')
                    # Clear the session variables related to OTP
                    del request.session['otp']
                    del request.session['otp_time']
                    return redirect('login')
                except Exception as e:
                    # Handle exceptions like duplicate username
                    messages.error(request, f'Error creating user: {e}')
            else:
                messages.error(request, 'Invalid OTP')
        else:
            messages.error(request, 'OTP verification failed. Please sign up again.')
            return redirect('signup')
    return render(request, 'registration/otp_verification.html')


if not firebase_admin._apps:
    cred_fp = str(Path.cwd()) + "\db_credentials.json"
    cred = credentials.Certificate(cred_fp)
    firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})

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


def reset_password_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(request=request)
            messages.success(request, 'An email has been sent with instructions to reset your password.')
            return redirect('login')
    else:
        form = PasswordResetForm()
    return render(request, 'registration/password_reset.html', {'form': form})

def reset_password_confirm(request, uidb64, token):
    # Add your password reset confirmation logic here
    pass