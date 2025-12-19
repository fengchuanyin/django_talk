from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse

# Create your views here.
def index(request):
    return HttpResponse('Hello World!')

def consumer(request):
    return render(request, 'consumer.html')

def merchant(request):
    return redirect(reverse('review_insights:dashboard'))
