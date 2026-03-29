from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Decision, Streak, Goal
from datetime import date, timedelta
from django.db.models import Count, Q
from django.utils import timezone
from django.contrib import messages
import csv
import random

MAX_GOALS_PER_DAY = 5
PRIORITY_OPTIONS = [
    ('study', '📚 Study'), ('health', '🏃 Health'),
    ('work', '💼 Work'), ('fun', '🎮 Fun'), ('other', '📌 Other'),
]


@login_required
def home(request):
    result = None
    reminder = None

    if request.method == "POST":
        action = request.POST.get("action", "decide")

        if action == "add_goal":
            text = request.POST.get("goal_text", "").strip()
            today_goals = Goal.objects.filter(user=request.user, created_at=date.today())
            if not text:
                messages.error(request, "Goal text cannot be empty.")
            elif today_goals.count() >= MAX_GOALS_PER_DAY:
                messages.error(request, f"Maximum {MAX_GOALS_PER_DAY} goals per day allowed.")
            elif len(text) > 200:
                messages.error(request, "Goal is too long (max 200 characters).")
            else:
                Goal.objects.create(user=request.user, text=text)
            return redirect('home')

        if action == "toggle_goal":
            goal_id = request.POST.get("goal_id")
            try:
                goal = Goal.objects.get(id=goal_id, user=request.user)
                goal.completed = not goal.completed
                goal.save()
            except Goal.DoesNotExist:
                pass
            return redirect('home')

        if action == "delete_goal":
            goal_id = request.POST.get("goal_id")
            Goal.objects.filter(id=goal_id, user=request.user).delete()
            return redirect('home')

        if action == "compare_tasks":
            task_a = request.POST.get("task_a", "").strip()
            task_b = request.POST.get("task_b", "").strip()
            try:
                urgency_a = max(1, min(5, int(request.POST.get("urgency_a", 3))))
                urgency_b = max(1, min(5, int(request.POST.get("urgency_b", 3))))
                impact_a  = max(1, min(5, int(request.POST.get("impact_a",  3))))
                impact_b  = max(1, min(5, int(request.POST.get("impact_b",  3))))
                effort_a  = max(1, min(5, int(request.POST.get("effort_a",  3))))
                effort_b  = max(1, min(5, int(request.POST.get("effort_b",  3))))
            except (ValueError, TypeError):
                messages.error(request, "Invalid slider values.")
                return redirect('home')
            deadline_a = request.POST.get("deadline_a", "no")
            deadline_b = request.POST.get("deadline_b", "no")
            score_a = _compare_score(urgency_a, impact_a, effort_a, deadline_a)
            score_b = _compare_score(urgency_b, impact_b, effort_b, deadline_b)
            if score_a > score_b:
                winner, loser, ws, ls = (task_a or "Task A"), (task_b or "Task B"), score_a, score_b
            elif score_b > score_a:
                winner, loser, ws, ls = (task_b or "Task B"), (task_a or "Task A"), score_b, score_a
            else:
                winner = loser = None
                ws = ls = score_a
            compare_result = {
                "task_a": task_a or "Task A", "task_b": task_b or "Task B",
                "score_a": score_a, "score_b": score_b,
                "winner": winner, "loser": loser,
                "winner_score": ws, "loser_score": ls, "is_tie": winner is None,
            }
            return render(request, "home.html", {
                "compare_result": compare_result,
                "decisions": Decision.objects.filter(user=request.user)[:5],
                "goals": Goal.objects.filter(user=request.user, created_at=date.today()),
                "suggestions": get_smart_suggestions(request.user),
                "streak": Streak.objects.filter(user=request.user).first(),
            })

        if action == "quick_decide":
            task = request.POST.get("task", "").strip()[:255]
            if not task:
                messages.error(request, "Task name is required.")
                return redirect('home')
            energy = request.POST.get("energy", "medium")
            if energy not in ('high', 'medium', 'low'):
                energy = 'medium'
            weights = {"high": [6, 3, 1], "medium": [4, 4, 2], "low": [2, 4, 4]}
            w = weights[energy]
            roll = random.randint(0, sum(w) - 1)
            if roll < w[0]:
                result = "DO IT"
            elif roll < w[0] + w[1]:
                result = "DELAY"
            else:
                result = "SKIP"
            if energy == "low" and result == "DO IT":
                result = "DO SMALL VERSION"
            priority = request.POST.get("priority", "other")
            if priority not in ('study', 'health', 'work', 'fun', 'other'):
                priority = 'other'
            Decision.objects.create(user=request.user, task=task, result=result,
                                    energy=energy, is_quick=True, priority=priority)
            _update_streak(request.user)
            return render(request, "home.html", {
                "result": result,
                "decisions": Decision.objects.filter(user=request.user)[:5],
                "goals": Goal.objects.filter(user=request.user, created_at=date.today()),
                "suggestions": get_smart_suggestions(request.user),
                "streak": Streak.objects.filter(user=request.user).first(),
                "reminder": _get_reminder(result),
            })

        # Standard decision
        task = request.POST.get("task", "").strip()[:255]
        if not task:
            messages.error(request, "Task name is required.")
            return redirect('home')
        score = 0
        answers = []
        for i in range(1, 6):
            val = request.POST.get(f"q{i}") == "on"
            answers.append(val)
            if val:
                score += 1
        energy = request.POST.get("energy", "medium")
        if energy not in ('high', 'medium', 'low'):
            energy = 'medium'
        priority = request.POST.get("priority", "other")
        if priority not in ('study', 'health', 'work', 'fun', 'other'):
            priority = 'other'
        if score >= 4:
            result = "DO IT"
        elif score >= 2:
            result = "DELAY"
        else:
            result = "SKIP"
        if energy == "low" and result == "DO IT":
            result = "DO SMALL VERSION"
        notes = request.POST.get("notes", "").strip()[:500]
        Decision.objects.create(
            user=request.user, task=task,
            q1=answers[0], q2=answers[1], q3=answers[2],
            q4=answers[3], q5=answers[4],
            result=result, energy=energy, priority=priority, notes=notes,
        )
        _update_streak(request.user)
        reminder = _get_reminder(result)

    return render(request, "home.html", {
        "result": result, "reminder": reminder,
        "decisions": Decision.objects.filter(user=request.user)[:5],
        "goals": Goal.objects.filter(user=request.user, created_at=date.today()),
        "streak": Streak.objects.filter(user=request.user).first(),
        "suggestions": get_smart_suggestions(request.user),
    })


def _update_streak(user):
    streak, _ = Streak.objects.get_or_create(user=user)
    today = date.today()
    if streak.last_used == today:
        return
    elif streak.last_used and (today - streak.last_used).days == 1:
        streak.count += 1
    else:
        streak.count = 1
    if streak.count > streak.best_streak:
        streak.best_streak = streak.count
    streak.last_used = today
    streak.save()


def _compare_score(urgency, impact, effort, has_deadline):
    effort_score = 6 - effort
    score = (urgency * 0.35) + (impact * 0.30) + (effort_score * 0.20)
    if has_deadline == "yes":
        score += 0.75
    return round(score, 2)


def get_smart_suggestions(user):
    suggestions = []
    today = date.today()
    now = timezone.now()
    all_decisions = Decision.objects.filter(user=user)
    week_decisions = all_decisions.filter(created_at__date__gte=today - timedelta(days=7))
    today_decisions = all_decisions.filter(created_at__date=today)
    total_week = week_decisions.count()

    if total_week == 0:
        suggestions.append({'icon': '👋', 'title': 'Welcome!',
                             'message': 'Start making decisions to get personalised insights.',
                             'severity': 'info', 'category': 'onboarding'})
        return suggestions

    for key, label, emoji in [('study', 'studying', '📚'), ('health', 'health tasks', '🏃'), ('work', 'work tasks', '💼')]:
        delayed = week_decisions.filter(Q(priority=key) | Q(task__icontains=key), result="DELAY").count()
        total_cat = week_decisions.filter(Q(priority=key) | Q(task__icontains=key)).count()
        if delayed >= 3:
            pct = round((delayed / max(total_cat, 1)) * 100)
            suggestions.append({'icon': emoji, 'title': f'You are avoiding {label}!',
                                 'message': f"Delayed {label} {delayed} times ({pct}%). Start now — even 10 min counts!",
                                 'severity': 'danger', 'category': 'procrastination'})

    skip_count = week_decisions.filter(result="SKIP").count()
    skip_pct = round((skip_count / total_week) * 100)
    if skip_count >= 5 and skip_pct >= 40:
        suggestions.append({'icon': '⛔', 'title': 'Too many tasks skipped!',
                             'message': f"Skipped {skip_count} tasks ({skip_pct}%). Try 'Do Small Version' instead.",
                             'severity': 'danger', 'category': 'skip_habit'})
    elif skip_count >= 3:
        suggestions.append({'icon': '🤔', 'title': 'Consider smaller steps',
                             'message': f"Skipped {skip_count} tasks this week. Small wins build momentum!",
                             'severity': 'warning', 'category': 'skip_habit'})

    for key, label, emoji in [('health', 'health', '💚'), ('study', 'study', '📖'), ('work', 'work', '📋')]:
        cat = week_decisions.filter(priority=key)
        if cat.count() >= 2 and cat.filter(result="SKIP").count() >= 2:
            suggestions.append({'icon': emoji, 'title': f'Neglecting {label} tasks',
                                 'message': f"Skipped {cat.filter(result='SKIP').count()} of {cat.count()} {label} tasks.",
                                 'severity': 'warning', 'category': 'neglect'})

    low_e = week_decisions.filter(energy="low").count()
    if low_e >= 4 and round((low_e / total_week) * 100) >= 50:
        suggestions.append({'icon': '🔋', 'title': 'Your energy is running low!',
                             'message': f"{round((low_e/total_week)*100)}% of decisions were low energy. More rest needed.",
                             'severity': 'warning', 'category': 'energy'})

    if today_decisions.count() >= 10:
        suggestions.append({'icon': '🧠', 'title': 'Decision fatigue alert!',
                             'message': f"Made {today_decisions.count()} decisions today. Take a break!",
                             'severity': 'warning', 'category': 'overload'})

    delay_count = week_decisions.filter(result="DELAY").count()
    do_count = week_decisions.filter(result__in=["DO IT", "DO SMALL VERSION"]).count()
    if delay_count >= 4 and do_count <= 1:
        suggestions.append({'icon': '⏰', 'title': 'Stuck in delay mode!',
                             'message': f"Delayed {delay_count} tasks but only completed {do_count}. Pick ONE now!",
                             'severity': 'danger', 'category': 'delay_loop'})

    fun = week_decisions.filter(priority="fun").count()
    productive = week_decisions.filter(priority__in=["study", "work", "health"]).count()
    if fun >= 4 and fun > productive:
        suggestions.append({'icon': '🎮', 'title': 'Fun is taking over!',
                             'message': f"{fun} fun vs {productive} productive tasks. Balance is key!",
                             'severity': 'warning', 'category': 'balance'})

    streak = Streak.objects.filter(user=user).first()
    if streak and streak.count >= 3 and streak.last_used != today:
        suggestions.append({'icon': '🔥', 'title': f'Your {streak.count}-day streak is at risk!',
                             'message': "Make at least one decision today to keep it alive.",
                             'severity': 'danger', 'category': 'streak'})

    incomplete = Goal.objects.filter(user=user, created_at=today, completed=False).count()
    if incomplete > 0 and now.hour >= 18:
        suggestions.append({'icon': '🎯', 'title': f'{incomplete} goal{"s" if incomplete > 1 else ""} still pending!',
                             'message': "The day is almost over. Push through before bed!",
                             'severity': 'warning', 'category': 'goals'})

    do_it_count = week_decisions.filter(result__in=["DO IT", "DO SMALL VERSION"]).count()
    do_pct = round((do_it_count / total_week) * 100)
    if do_it_count >= 7 and do_pct >= 60:
        suggestions.append({'icon': '🚀', 'title': "You're on fire!",
                             'message': f"Completed {do_it_count} tasks ({do_pct}% action rate). Keep it up!",
                             'severity': 'success', 'category': 'positive'})
    elif do_it_count >= 3 and do_pct >= 50:
        suggestions.append({'icon': '💪', 'title': 'Great progress!',
                             'message': f"{do_pct}% action rate this week. Stay consistent!",
                             'severity': 'success', 'category': 'positive'})

    active_days = week_decisions.dates('created_at', 'day').count()
    if total_week >= 3 and active_days <= 2:
        suggestions.append({'icon': '📅', 'title': 'Be more consistent',
                             'message': f"Used the app only {active_days} days this week. Daily check-ins help!",
                             'severity': 'info', 'category': 'consistency'})

    repeated = week_decisions.filter(result__in=["DELAY", "SKIP"]).values('task').annotate(
        count=Count('id')).filter(count__gte=2).order_by('-count')[:1]
    for t in repeated:
        suggestions.append({'icon': '🔄', 'title': f'"{t["task"]}" keeps coming back',
                             'message': f"Delayed/skipped {t['count']} times. Do it or remove it!",
                             'severity': 'danger', 'category': 'repeated'})

    order = {'danger': 0, 'warning': 1, 'info': 2, 'success': 3}
    suggestions.sort(key=lambda s: order.get(s['severity'], 99))
    return suggestions[:5]


def _get_reminder(result):
    return {
        "DO IT": "⚡ Start NOW! Don't wait — momentum is everything.",
        "DO SMALL VERSION": "🎯 Do a 15-min version right now. Small wins count!",
        "DELAY": "⏰ Set a reminder to revisit this in 1 hour.",
        "SKIP": "✅ Good call. Focus your energy on what matters.",
    }.get(result)


@login_required
def history(request):
    filter_type = request.GET.get('filter', 'all')
    priority = request.GET.get('priority', '')
    search = request.GET.get('search', '').strip()

    decisions = Decision.objects.filter(user=request.user)
    if filter_type != 'all':
        decisions = decisions.filter(result=filter_type.upper().replace('-', ' '))
    if priority:
        decisions = decisions.filter(priority=priority)
    if search:
        decisions = decisions.filter(task__icontains=search)

    return render(request, "history.html", {
        "decisions": decisions, "filter": filter_type,
        "priority": priority, "search": search,
        "priority_options": PRIORITY_OPTIONS,
    })


@login_required
def toggle_bookmark(request, pk):
    d = get_object_or_404(Decision, pk=pk, user=request.user)
    d.bookmarked = not d.bookmarked
    d.save()
    return redirect('history')


@login_required
def export_csv(request):
    decisions = Decision.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="decisions.csv"'
    writer = csv.writer(response)
    writer.writerow(['Task', 'Result', 'Energy', 'Priority', 'Notes', 'Date', 'Bookmarked'])
    for d in decisions:
        writer.writerow([d.task, d.result, d.energy, d.priority, d.notes,
                         d.created_at.strftime('%Y-%m-%d %H:%M'), 'Yes' if d.bookmarked else 'No'])
    return response


@login_required
def delete_decision(request, pk):
    if request.method == "POST":
        d = get_object_or_404(Decision, pk=pk, user=request.user)
        d.delete()
        messages.success(request, "Decision deleted.")
    return redirect('history')
