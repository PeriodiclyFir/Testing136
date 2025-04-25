from django.urls import path
from . import views

urlpatterns = [
    path("dummypage", views.dummypage, name="dummypage"),
    path("time", views.current_time, name="current_time"),
    path("sum", views.add_numbers, name="add_numbers"),
]