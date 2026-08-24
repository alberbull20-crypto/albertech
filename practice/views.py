from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Challenge, ChallengeCompletion


@login_required
def challenge_list(request):
    difficulty = request.GET.get("difficulty", "")
    challenges = Challenge.objects.all()
    if difficulty:
        challenges = challenges.filter(difficulty=difficulty)

    completed_ids = set(
        ChallengeCompletion.objects.filter(user=request.user).values_list("challenge_id", flat=True)
    )
    for c in challenges:
        c.is_completed = c.id in completed_ids

    total = Challenge.objects.count()
    completed_count = len(completed_ids)

    return render(request, "practice/challenge_list.html", {
        "challenges": challenges,
        "selected_difficulty": difficulty,
        "total": total,
        "completed_count": completed_count,
    })


@login_required
def challenge_detail(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    result = None
    submitted_answer = ""

    if request.method == "POST":
        submitted_answer = request.POST.get("answer", "").strip()
        is_correct = submitted_answer.lower() == challenge.expected_answer.strip().lower()
        result = "correct" if is_correct else "incorrect"
        if is_correct:
            ChallengeCompletion.objects.get_or_create(user=request.user, challenge=challenge)

    is_completed = ChallengeCompletion.objects.filter(user=request.user, challenge=challenge).exists()

    return render(request, "practice/challenge_detail.html", {
        "challenge": challenge,
        "result": result,
        "submitted_answer": submitted_answer,
        "is_completed": is_completed,
    })