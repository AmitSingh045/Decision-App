from django.shortcuts import render, redirect
from core.models import Decision, Streak
from core.views import get_smart_suggestions
from datetime import date, timedelta
from django.db.models import Count
import json


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    decisions = Decision.objects.filter(user=request.user)
    today = date.today()
    week_ago = today - timedelta(days=7)

    # Basic counts
    total = decisions.count()
    do_it = decisions.filter(result__in=["DO IT", "DO SMALL VERSION"]).count()
    delay = decisions.filter(result="DELAY").count()
    skip = decisions.filter(result="SKIP").count()

    # Streak
    streak = Streak.objects.filter(user=request.user).first()

    # Today's decisions
    today_decisions = decisions.filter(created_at__date=today)
    today_count = today_decisions.count()
    today_do = today_decisions.filter(result__in=["DO IT", "DO SMALL VERSION"]).count()

    # Productivity score (% of DO IT decisions this week)
    week_decisions = decisions.filter(created_at__date__gte=week_ago)
    week_total = week_decisions.count()
    week_do = week_decisions.filter(result__in=["DO IT", "DO SMALL VERSION"]).count()
    productivity = round((week_do / week_total) * 100) if week_total > 0 else 0

    # Weekly chart data (last 7 days)
    chart_labels = []
    chart_do = []
    chart_delay = []
    chart_skip = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        chart_labels.append(d.strftime('%a'))
        day_decisions = decisions.filter(created_at__date=d)
        chart_do.append(day_decisions.filter(result__in=["DO IT", "DO SMALL VERSION"]).count())
        chart_delay.append(day_decisions.filter(result="DELAY").count())
        chart_skip.append(day_decisions.filter(result="SKIP").count())

    # Priority breakdown
    priority_data = decisions.values('priority').annotate(count=Count('id'))
    priority_labels = [p['priority'].title() for p in priority_data]
    priority_counts = [p['count'] for p in priority_data]

    # Decision patterns
    patterns = []
    for pri in ['study', 'health', 'work', 'fun']:
        pri_decisions = decisions.filter(priority=pri)
        if pri_decisions.exists():
            skip_pct = pri_decisions.filter(result="SKIP").count() / pri_decisions.count() * 100
            if skip_pct >= 50:
                patterns.append(f"⚠️ You skip {pri} tasks {int(skip_pct)}% of the time.")
            do_pct = pri_decisions.filter(result__in=["DO IT", "DO SMALL VERSION"]).count() / pri_decisions.count() * 100
            if do_pct >= 70:
                patterns.append(f"🔥 You're crushing it on {pri} tasks! ({int(do_pct)}% action rate)")

    # Smart Suggestions
    suggestions = get_smart_suggestions(request.user)

    return render(request, "dashboard.html", {
        "total": total,
        "do_it": do_it,
        "delay": delay,
        "skip": skip,
        "streak": streak,
        "today_count": today_count,
        "today_do": today_do,
        "productivity": productivity,
        "chart_labels": json.dumps(chart_labels),
        "chart_do": json.dumps(chart_do),
        "chart_delay": json.dumps(chart_delay),
        "chart_skip": json.dumps(chart_skip),
        "priority_labels": json.dumps(priority_labels),
        "priority_counts": json.dumps(priority_counts),
        "patterns": patterns,
        "suggestions": suggestions,
    })