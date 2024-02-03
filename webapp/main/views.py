from django.shortcuts import render

# Views
def home(request):
    return render(request, 'main/home.html')

def stats(request):
    return render(request, 'main/stats.html')