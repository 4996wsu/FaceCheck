from django.shortcuts import render, redirect
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

# Create your views here.
def home(request):
    return render(request, 'main/home.html')

def stats(request):
    return render(request, 'main/stats.html')
def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Don't save the user yet
            otp = random.randint(100000, 999999)  # Generate a 6-digit OTP
            request.session['otp'] = otp  # Store the OTP in the session
            request.session['username'] = form.cleaned_data.get('username')
            request.session['email'] = form.cleaned_data.get('email')
            request.session['password'] = form.cleaned_data.get('password1')
            request.session['otp_time'] = str(datetime.now())  # Store the current time
            send_mail(
                'Your OTP',
                f'Your OTP is {otp}',
                'facecheckwayne@gmail.com',
                [form.cleaned_data.get('email')],
                fail_silently=False,
            )
            return redirect('otp_verification')  # Redirect to OTP verification view
        else:
            print(form.errors)
    else:
        form = RegisterForm()
    return render(request, 'registration/sign_up.html', {'form': form})



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
                    return redirect('list_report')
                except Exception as e:
                    # Handle exceptions like duplicate username
                    messages.error(request, f'Error creating user: {e}')
            else:
                messages.error(request, 'Invalid OTP')
        else:
            messages.error(request, 'OTP verification failed. Please sign up again.')
            return redirect('signup')

    return render(request, 'registration/otp_verification.html')

