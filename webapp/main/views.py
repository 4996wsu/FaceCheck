from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.tokens import default_token_generator
from database import update_student_photo, add_student
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from preprocess import detect_and_crop_face, face_encode, make_pt_file
from django.contrib.auth.forms import PasswordResetForm
from .forms import RegisterForm
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
import firebase_admin
from firebase_admin import credentials, storage
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetCompleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
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
from django.urls import reverse
from django.contrib.messages import get_messages

# Create your views here.
class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset.html'

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetComplete(PasswordResetCompleteView):
    template_name = 'registration/password_done.html'

def home(request):
    return render(request, 'main/home.html')

def stats(request):
    return render(request, 'main/stats.html')

def manageclass(request):
    return render(request, 'main/manageclass.html')


def clear_messages(request):
    storage = get_messages(request)
    for message in storage:
        pass

def sign_up(request):
    clear_messages(request)
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            clear_messages(request)
            user = form.save(commit=False)  # Don't save the user yet
            otp = random.randint(100000, 999999)  # Generate a 6-digit OTP
            request.session['otp'] = otp  # Store the OTP in the session
            request.session['username'] = form.cleaned_data.get('username')
            #request.session['email'] = form.cleaned_data.get('email')
            request.session['email'] = form.cleaned_data.get('username') + '@wayne.edu'
            request.session['password'] = form.cleaned_data.get('password1')
            request.session['first_name'] = form.cleaned_data.get('first_name')
            request.session['last_name'] = form.cleaned_data.get('last_name')
            request.session['otp_time'] = str(datetime.now())  # Store the current time
            
            send_mail(
                'Verification Code',
                f'Your verification code is {otp}.\nDo not share this information with anyone else.',
                settings.DEFAULT_FROM_EMAIL,
                [request.session['email']],
                fail_silently=False,
            )
            return redirect('otp_verification')  # Redirect to OTP verification view
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()
    return render(request, 'registration/sign_up.html', {'form': form})

def otp_verification(request):
    clear_messages(request)
    if request.method == 'POST':
        otp = request.POST.get('otp')
        otp_time_str = request.session.get('otp_time')
        if otp_time_str:
            otp_time = datetime.strptime(otp_time_str, '%Y-%m-%d %H:%M:%S.%f')
            if datetime.now() - otp_time > timedelta(minutes=2):  # Check if more than 2 minutes have passed
                messages.error(request, 'OTP expired. Please sign up again.')
                # Redirect to the signup page
                return redirect('sign-up')
            elif otp == str(request.session.get('otp')):
                try:
                    User.objects.create_user(
                        username=request.session.get('username'),
                        email=request.session.get('email'),
                        password=request.session.get('password'),
                        first_name=request.session.get('first_name'),
                        last_name=request.session.get('last_name')
                    )
                    # Add user to firebase
                    add_student(request.session.get('username'), request.session.get('first_name'), request.session.get('last_name'))
                    
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
            print("result", result)
            delete_file_from_firebase(image.name)
            # Success message and error handling        
            
            if result == "error":
                messages.warning(request, 'Photo is invalid. Please upload a photo with one face in it.')
            elif result == 'flagged':
                messages.warning(request, "Your photo has matched with another person's photo. Please resolve it with your professors.")
            elif result == 'unknown':
                messages.success(request, 'Successfully uploaded photo.')
            
            return render(request, 'main/enrollment.html', {'form': form})

        else:
            return HttpResponse("Invalid form.")
    else:
        form = ImageUploadForm()
    return render(request, 'main/enrollment.html', {'form': form})

