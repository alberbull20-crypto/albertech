import io
import os
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from .models import Course, Lesson, LessonProgress, LessonNote, Enrollment


def course_list(request):
    level = request.GET.get("level", "")
    query = request.GET.get("q", "")

    courses = Course.objects.prefetch_related("modules__lessons")
    if level:
        courses = courses.filter(level=level)
    if query:
        courses = courses.filter(Q(title__icontains=query) | Q(description__icontains=query))

    enrolled_ids = set()
    if request.user.is_authenticated:
        enrolled_ids = set(
            Enrollment.objects.filter(user=request.user).values_list("course_id", flat=True)
        )

    for course in courses:
        course.thumbnail = None
        for module in course.modules.all():
            for lesson in module.lessons.all():
                if lesson.youtube_video_id:
                    course.thumbnail = f"https://img.youtube.com/vi/{lesson.youtube_video_id}/hqdefault.jpg"
                    break
            if course.thumbnail:
                break
        course.is_enrolled = course.id in enrolled_ids

    return render(request, "courses/course_list.html", {
        "courses": courses,
        "selected_level": level,
        "query": query,
        "student_count": User.objects.count(),
        "course_count": Course.objects.count(),
    })


def about(request):
    return render(request, "courses/about.html")


@login_required
def course_player(request, slug):
    course = get_object_or_404(Course, slug=slug)
    Enrollment.objects.get_or_create(user=request.user, course=course)

    modules = course.modules.prefetch_related("lessons").all()

    all_lessons = []
    for module in modules:
        for lesson in module.lessons.all():
            all_lessons.append(lesson)
            lesson.thumbnail = (
                f"https://img.youtube.com/vi/{lesson.youtube_video_id}/mqdefault.jpg"
                if lesson.youtube_video_id else None
            )

    completed_ids = set(
        LessonProgress.objects.filter(user=request.user, lesson__in=all_lessons)
        .values_list("lesson_id", flat=True)
    )

    active_lesson = None
    requested_id = request.GET.get("lesson")
    previous_completed = True
    for lesson in all_lessons:
        lesson.is_completed = lesson.id in completed_ids
        lesson.is_locked = not previous_completed
        previous_completed = lesson.is_completed

        if requested_id and str(lesson.id) == requested_id and not lesson.is_locked:
            active_lesson = lesson

    if not active_lesson:
        for lesson in all_lessons:
            if not lesson.is_completed and not lesson.is_locked:
                active_lesson = lesson
                break

    if not active_lesson and all_lessons:
        active_lesson = all_lessons[-1]

    percent = 0
    if all_lessons:
        percent = round(sum(1 for l in all_lessons if l.is_completed) / len(all_lessons) * 100)

    note_text = ""
    resources = []
    if active_lesson:
        resources = active_lesson.resources.all()
        note = LessonNote.objects.filter(user=request.user, lesson=active_lesson).first()
        if note:
            note_text = note.content

    return render(request, "courses/course_player.html", {
        "course": course,
        "modules": modules,
        "active_lesson": active_lesson,
        "percent": percent,
        "note_text": note_text,
        "resources": resources,
    })


@login_required
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    Enrollment.objects.get_or_create(user=request.user, course=course)
    return redirect("courses:course_player", slug=slug)


@login_required
def toggle_lesson_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.module.course
    progress, created = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)

    if not created:
        progress.delete()
        return redirect(f"{reverse('courses:course_player', args=[course.slug])}?lesson={lesson.id}")

    modules = course.modules.prefetch_related("lessons").all()
    all_lessons = []
    for module in modules:
        for l in module.lessons.all():
            all_lessons.append(l)

    next_lesson = None
    found_current = False
    for l in all_lessons:
        if found_current:
            next_lesson = l
            break
        if l.id == lesson.id:
            found_current = True

    target_id = next_lesson.id if next_lesson else lesson.id
    return redirect(f"{reverse('courses:course_player', args=[course.slug])}?lesson={target_id}")


@login_required
def save_note(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == "POST":
        content = request.POST.get("content", "")
        LessonNote.objects.update_or_create(
            user=request.user, lesson=lesson, defaults={"content": content}
        )
    return redirect(f"{reverse('courses:course_player', args=[lesson.module.course.slug])}?lesson={lesson.id}")


def _generate_certificate_pdf(user, course):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    BG = HexColor("#070B14")
    CYAN = HexColor("#3DD6E0")
    WHITE = HexColor("#E8F1F4")
    GRAY = HexColor("#7C93A3")

    # Background
    p.setFillColor(BG)
    p.rect(0, 0, width, height, fill=1, stroke=0)

    # Double border frame
    p.setStrokeColor(CYAN)
    p.setLineWidth(2)
    outer_margin = 28
    p.rect(outer_margin, outer_margin, width - 2 * outer_margin, height - 2 * outer_margin, fill=0, stroke=1)
    p.setLineWidth(1)
    inner_margin = 40
    p.rect(inner_margin, inner_margin, width - 2 * inner_margin, height - 2 * inner_margin, fill=0, stroke=1)

    center_x = width / 2

    # Logo
    logo_path = settings.BASE_DIR / "courses" / "static" / "courses" / "logo.png"
    if os.path.exists(logo_path):
        try:
            logo = ImageReader(str(logo_path))
            logo_size = 60
            p.drawImage(logo, center_x - logo_size / 2, height - 115, width=logo_size, height=logo_size,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Brand name + tagline
    p.setFillColor(WHITE)
    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(center_x, height - 140, "ALBERTECH")

    p.setFillColor(CYAN)
    p.setFont("Helvetica", 10)
    p.drawCentredString(center_x, height - 156, "Engineered for Tomorrow")

    p.setStrokeColor(CYAN)
    p.setLineWidth(1)
    p.line(center_x - 60, height - 165, center_x + 60, height - 165)

    # Title
    p.setFillColor(WHITE)
    p.setFont("Helvetica-Bold", 26)
    p.drawCentredString(center_x, height - 210, "CERTIFICATE OF COMPLETION")

    p.setStrokeColor(CYAN)
    p.line(center_x - 90, height - 222, center_x + 90, height - 222)

    # Body
    p.setFillColor(GRAY)
    p.setFont("Helvetica", 13)
    p.drawCentredString(center_x, height - 260, "This is to certify that")

    full_name = user.username
    if user.first_name:
        full_name = f"{user.first_name} {user.last_name}".strip()
    if hasattr(user, "profile") and user.profile.full_name():
        full_name = user.profile.full_name()

    p.setFillColor(CYAN)
    p.setFont("Helvetica-Bold", 28)
    p.drawCentredString(center_x, height - 300, full_name)
    name_width = p.stringWidth(full_name, "Helvetica-Bold", 28)
    p.setStrokeColor(CYAN)
    p.line(center_x - name_width / 2 - 10, height - 310, center_x + name_width / 2 + 10, height - 310)

    p.setFillColor(GRAY)
    p.setFont("Helvetica", 13)
    p.drawCentredString(center_x, height - 335, "has successfully completed the program")

    p.setFillColor(CYAN)
    p.setFont("Helvetica-Bold", 19)
    p.drawCentredString(center_x, height - 365, course.title)

    p.setFillColor(GRAY)
    p.setFont("Helvetica", 11)
    p.drawCentredString(center_x, height - 388, "demonstrating proficiency in coding, innovation, and problem-solving")

    # Date + Authorized By
    footer_y = 110
    left_x = width * 0.28
    right_x = width * 0.72

    p.setFillColor(CYAN)
    p.setFont("Helvetica-Bold", 9)
    p.drawCentredString(left_x, footer_y + 22, "DATE")
    p.drawCentredString(right_x, footer_y + 22, "AUTHORIZED BY")

    p.setFillColor(WHITE)
    p.setFont("Helvetica", 12)
    date_str = datetime.now().strftime("%B %d, %Y")
    p.drawCentredString(left_x, footer_y + 5, date_str)
    p.drawCentredString(right_x, footer_y + 5, "Albertech Systems")

    p.setStrokeColor(CYAN)
    p.setLineWidth(0.8)
    p.line(left_x - 55, footer_y - 3, left_x + 55, footer_y - 3)
    p.line(right_x - 55, footer_y - 3, right_x + 55, footer_y - 3)

    # Footer tagline
    p.setFillColor(CYAN)
    p.setFont("Helvetica-Oblique", 9)
    p.drawCentredString(center_x, 55, "Solve. Build. Lead.  •  Albertech Systems  •  Code Camp Certificate")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


def _course_is_completed(user, course):
    all_lessons = Lesson.objects.filter(module__course=course)
    total = all_lessons.count()
    completed = LessonProgress.objects.filter(user=user, lesson__in=all_lessons).count()
    return total > 0 and completed == total


@login_required
def download_certificate(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if not _course_is_completed(request.user, course):
        return redirect("courses:course_player", slug=slug)

    buffer = _generate_certificate_pdf(request.user, course)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{course.slug}-certificate.pdf"'
    return response


@login_required
def email_certificate(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if not _course_is_completed(request.user, course):
        return redirect("courses:course_player", slug=slug)

    buffer = _generate_certificate_pdf(request.user, course)

    email = EmailMessage(
        subject=f"Your Albertech Certificate — {course.title}",
        body=f"Congratulations on completing {course.title}!\n\nYour certificate is attached.\n\n— Albertech",
        to=[request.user.email],
    )
    email.attach(f"{course.slug}-certificate.pdf", buffer.getvalue(), "application/pdf")
    email.send()

    return redirect("courses:course_player", slug=slug)


@login_required
def dashboard(request):
    enrollments = Enrollment.objects.filter(user=request.user).select_related("course")

    enrolled_count = enrollments.count()
    completed_count = 0
    total_percent = 0
    course_progress = []

    for enrollment in enrollments:
        course = enrollment.course
        all_lessons = Lesson.objects.filter(module__course=course)
        total = all_lessons.count()
        completed = LessonProgress.objects.filter(user=request.user, lesson__in=all_lessons).count()
        percent = round((completed / total) * 100) if total else 0

        if percent == 100:
            completed_count += 1

        total_percent += percent
        course_progress.append({
            "course": course,
            "percent": percent,
            "enrolled_at": enrollment.enrolled_at,
        })

    overall_progress = round(total_percent / enrolled_count) if enrolled_count else 0
    certificates_earned = completed_count

    activity = []
    for enrollment in enrollments:
        activity.append({
            "title": "Started New Course",
            "subtitle": enrollment.course.title,
            "timestamp": enrollment.enrolled_at,
        })

    recent_progress = (
        LessonProgress.objects.filter(user=request.user)
        .select_related("lesson__module__course")
        .order_by("-completed_at")[:20]
    )
    for progress in recent_progress:
        activity.append({
            "title": "Completed Lesson",
            "subtitle": f"{progress.lesson.title} — {progress.lesson.module.course.title}",
            "timestamp": progress.completed_at,
        })

    activity.sort(key=lambda a: a["timestamp"], reverse=True)
    activity = activity[:8]

    return render(request, "courses/dashboard.html", {
        "enrolled_count": enrolled_count,
        "overall_progress": overall_progress,
        "completed_count": completed_count,
        "certificates_earned": certificates_earned,
        "course_progress": course_progress,
        "activity": activity,
    })


def coming_soon(request, feature_name):
    return render(request, "courses/coming_soon.html", {"feature_name": feature_name})