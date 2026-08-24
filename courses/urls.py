from django.urls import path
from . import views

app_name = "courses"
urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("about/", views.about, name="about"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("coming-soon/<str:feature_name>/", views.coming_soon, name="coming_soon"),
    path("lesson/<int:lesson_id>/toggle/", views.toggle_lesson_complete, name="toggle_lesson_complete"),
    path("lesson/<int:lesson_id>/note/", views.save_note, name="save_note"),
    path("<slug:slug>/enroll/", views.enroll_course, name="enroll_course"),
    path("<slug:slug>/certificate/", views.download_certificate, name="download_certificate"),
    path("<slug:slug>/certificate/email/", views.email_certificate, name="email_certificate"),
    path("<slug:slug>/", views.course_player, name="course_player"),
]