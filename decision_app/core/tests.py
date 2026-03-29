from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Decision, Streak, Goal
from .views import get_smart_suggestions, _compare_score
from datetime import date, timedelta


class DecisionLogicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')

    def test_score_4_gives_do_it(self):
        c = Client()
        c.login(username='testuser', password='testpass123')
        c.post(reverse('home'), {
            'action': 'decide', 'task': 'Test task',
            'q1': 'on', 'q2': 'on', 'q3': 'on', 'q4': 'on', 'q5': 'off',
            'energy': 'high', 'priority': 'work',
        })
        d = Decision.objects.filter(user=self.user).first()
        self.assertEqual(d.result, 'DO IT')

    def test_low_energy_do_it_becomes_small_version(self):
        c = Client()
        c.login(username='testuser', password='testpass123')
        c.post(reverse('home'), {
            'action': 'decide', 'task': 'Test',
            'q1': 'on', 'q2': 'on', 'q3': 'on', 'q4': 'on', 'q5': 'on',
            'energy': 'low', 'priority': 'work',
        })
        d = Decision.objects.filter(user=self.user).first()
        self.assertEqual(d.result, 'DO SMALL VERSION')

    def test_score_0_gives_skip(self):
        c = Client()
        c.login(username='testuser', password='testpass123')
        c.post(reverse('home'), {
            'action': 'decide', 'task': 'Skip this',
            'q1': 'off', 'q2': 'off', 'q3': 'off', 'q4': 'off', 'q5': 'off',
            'energy': 'high', 'priority': 'other',
        })
        d = Decision.objects.filter(user=self.user).first()
        self.assertEqual(d.result, 'SKIP')

    def test_compare_score_deadline_bonus(self):
        score_no  = _compare_score(3, 3, 3, 'no')
        score_yes = _compare_score(3, 3, 3, 'yes')
        self.assertGreater(score_yes, score_no)

    def test_compare_score_low_effort_higher_priority(self):
        easy = _compare_score(3, 3, 1, 'no')
        hard = _compare_score(3, 3, 5, 'no')
        self.assertGreater(easy, hard)


class StreakTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='streakuser', password='testpass123')

    def test_streak_increments_on_consecutive_days(self):
        streak = Streak.objects.create(user=self.user, count=3,
                                        last_used=date.today() - timedelta(days=1))
        from core.views import _update_streak
        _update_streak(self.user)
        streak.refresh_from_db()
        self.assertEqual(streak.count, 4)

    def test_streak_resets_after_gap(self):
        streak = Streak.objects.create(user=self.user, count=5,
                                        last_used=date.today() - timedelta(days=3))
        from core.views import _update_streak
        _update_streak(self.user)
        streak.refresh_from_db()
        self.assertEqual(streak.count, 1)

    def test_best_streak_is_preserved(self):
        streak = Streak.objects.create(user=self.user, count=10, best_streak=10,
                                        last_used=date.today() - timedelta(days=3))
        from core.views import _update_streak
        _update_streak(self.user)
        streak.refresh_from_db()
        self.assertEqual(streak.best_streak, 10)


class AuthTests(TestCase):
    def test_redirect_to_login_when_unauthenticated(self):
        c = Client()
        r = c.get(reverse('home'))
        self.assertRedirects(r, f"/login/?next=/")

    def test_register_and_login(self):
        c = Client()
        c.post(reverse('register'), {'username': 'newuser', 'password': 'secure1234', 'password2': 'secure1234'})
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_short_password_rejected(self):
        c = Client()
        c.post(reverse('register'), {'username': 'baduser', 'password': 'abc', 'password2': 'abc'})
        self.assertFalse(User.objects.filter(username='baduser').exists())

    def test_password_mismatch_rejected(self):
        c = Client()
        c.post(reverse('register'), {'username': 'mismatch', 'password': 'secure1234', 'password2': 'different123'})
        self.assertFalse(User.objects.filter(username='mismatch').exists())


class ExportCSVTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='csvuser', password='testpass123')
        Decision.objects.create(user=self.user, task='Test', result='DO IT', energy='high', priority='work')

    def test_export_csv_returns_200(self):
        c = Client()
        c.login(username='csvuser', password='testpass123')
        r = c.get(reverse('export_csv'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'text/csv')
