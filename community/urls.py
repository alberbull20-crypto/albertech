from django.urls import path
from . import views

app_name = "community"
urlpatterns = [
    path("", views.thread_list, name="thread_list"),
    path("new/", views.new_thread, name="new_thread"),
    path("<int:thread_id>/", views.thread_detail, name="thread_detail"),
    path("<int:thread_id>/reply/", views.add_reply, name="add_reply"),
]