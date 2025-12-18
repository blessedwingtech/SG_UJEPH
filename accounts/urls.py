from django.urls import path
from . import views

app_name = 'accounts'  # optionnel mais pratique pour les namespaces

urlpatterns = [
    # Gestion administrateurs
    path('admins/ajouter/', views.creer_admin, name='creer_admin'),  # 

    # Gestion étudiants
    path('etudiants/', views.liste_etudiants, name='liste_etudiants'),
    path('etudiants/ajouter/', views.creer_etudiant, name='creer_etudiant'),
    path('etudiants/recherche/', views.rechercher_etudiants_ajax, name='recherche_etudiants_ajax'),
    path('etudiants/export/', views.export_etudiants_csv, name='export_etudiants_csv'),
    path('professeurs/export/', views.export_professeurs_csv, name='export_professeurs_csv'),


    # Gestion professeurs
    path('professeurs/', views.liste_professeurs, name='liste_professeurs'),
    path('professeurs/ajouter/', views.creer_professeur, name='creer_professeur'),
    path('professeurs/recherche/', views.rechercher_professeurs_ajax, name='recherche_professeurs_ajax'),

    path('etudiants/<int:etudiant_id>/modifier/', views.modifier_etudiant, name='modifier_etudiant'),
    path('etudiants/<int:etudiant_id>/supprimer/', views.supprimer_etudiant, name='supprimer_etudiant'),
    path('professeurs/<int:professeur_id>/modifier/', views.modifier_professeur, name='modifier_professeur'),
    path('professeurs/<int:professeur_id>/supprimer/', views.supprimer_professeur, name='supprimer_professeur'),

    path('users/gestion_utilisateurs', views.gestion_utilisateurs, name='gestion_utilisateurs'),
    path('utilisateur/<int:user_id>/', views.detail_utilisateur, name='detail_utilisateur'),
    path('users/<int:user_id>/toggle_activation', views.toggle_activation, name='toggle_activation'),
    path('utilisateur/<int:user_id>/changer-role/', views.changer_role, name='changer_role'),
     
    # Authentification et dashboard
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('check-username/', views.check_username, name='check_username'),
    path('logout/confirm/', views.logout_confirm, name='logout_confirm'),  # ✅ AJOUT
    path('change-password-required/', views.change_password_required, name='change_password_required'),  # ✅ AJOUT
    path('dashboard/', views.dashboard, name='dashboard'),
    path('mon-profil/', views.mon_profil, name='mon_profil'),
]
