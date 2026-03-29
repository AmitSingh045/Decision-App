from django.contrib import admin
from django.urls import path
from accounts.views import register, user_login, user_logout
from core.views import home, history, toggle_bookmark, export_csv, delete_decision
from dashboard.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name="home"),
    path('dashboard/', dashboard, name="dashboard"),
    path('history/', history, name="history"),
    path('history/export/', export_csv, name="export_csv"),
    path('bookmark/<int:pk>/', toggle_bookmark, name="toggle_bookmark"),
    path('delete/<int:pk>/', delete_decision, name="delete_decision"),
    path('register/', register, name="register"),
    path('login/', user_login, name="login"),
    path('logout/', user_logout, name="logout"),
]
