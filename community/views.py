from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Thread, Reply


def thread_list(request):
    category = request.GET.get("category", "")
    threads = Thread.objects.select_related("author").prefetch_related("replies")
    if category:
        threads = threads.filter(category=category)

    for thread in threads:
        thread.reply_count = thread.replies.count()

    return render(request, "community/thread_list.html", {
        "threads": threads,
        "selected_category": category,
        "categories": Thread.CATEGORY_CHOICES,
    })


def thread_detail(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    replies = thread.replies.select_related("author").all()
    return render(request, "community/thread_detail.html", {"thread": thread, "replies": replies})


@login_required
def new_thread(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        category = request.POST.get("category", "general")
        if title and content:
            thread = Thread.objects.create(author=request.user, title=title, content=content, category=category)
            return redirect("community:thread_detail", thread_id=thread.id)
    return render(request, "community/new_thread.html", {"categories": Thread.CATEGORY_CHOICES})


@login_required
def add_reply(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Reply.objects.create(thread=thread, author=request.user, content=content)
    return redirect("community:thread_detail", thread_id=thread.id)