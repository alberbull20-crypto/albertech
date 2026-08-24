from django.contrib import admin
from .models import Course, Module, Lesson, LessonProgress, LessonNote, LessonResource, Enrollment 

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "order", "youtube_video_id", "duration_minutes")
    list_filter = ("module__course", "module")

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "enrolled_at")
    list_filter = ("course", "enrolled_at")


admin.site.register(Course)
admin.site.register(Module)
admin.site.register(LessonProgress)
admin.site.register(LessonNote)
admin.site.register(LessonResource)