# grades/urls.py
from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    # Professeur
    path('saisie-notes/<int:cours_id>/', views.saisie_notes, name='saisie_notes'),
    
    # Admin
    path('validation-notes/', views.validation_notes, name='validation_notes'),
    path('validation-notes/<int:cours_id>/traiter/', views.traiter_cours_notes, name='traiter_cours_notes'),
    path('notes-publiees/', views.gestion_notes_publiees, name='gestion_notes_publiees'),
    path('remettre-brouillon/<int:cours_id>/', views.remettre_notes_brouillon, name='remettre_notes_brouillon'),
    # Étudiant
    path('mes-notes/', views.consulter_notes_etudiant, name='consulter_notes_etudiant'),

    path('gestion-semestres/', views.gestion_semestres, name='gestion_semestres'),
]