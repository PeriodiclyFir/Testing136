from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse
import datetime

def dummypage(request):
    if request.method == "GET":
        return HttpResponse("No content here, sorry!")

def current_time(request):
    utc_now = datetime.datetime.utcnow()
    cdt_now = utc_now - datetime.timedelta(hours=5)
    return HttpResponse(cdt_now.strftime("%H:%M"))

def add_numbers(request):
    try:
        n1 = float(request.GET.get("n1", 0))
        n2 = float(request.GET.get("n2", 0))
        return HttpResponse(str(n1 + n2))
    except Exception as e:
        return HttpResponse(f"Error: {e}")