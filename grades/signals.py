# Dans signals.py de l'application grades
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Note, InscriptionCours

@receiver(post_save, sender=Note)
def create_inscription_on_note_creation(sender, instance, created, **kwargs):
    """
    Crée automatiquement une inscription quand une note est créée
    pour un étudiant qui n'est pas encore inscrit au cours
    """
    if created:
        # Vérifier si l'inscription existe déjà
        inscription_exists = InscriptionCours.objects.filter(
            etudiant=instance.etudiant,
            cours=instance.cours
        ).exists()
        
        if not inscription_exists:
            # Créer l'inscription manquante
            InscriptionCours.objects.create(
                etudiant=instance.etudiant,
                cours=instance.cours
            )
            print(f"✅ Inscription créée pour {instance.etudiant} au cours {instance.cours}")