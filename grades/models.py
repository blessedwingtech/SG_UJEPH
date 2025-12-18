from django.db import models
from accounts.models import Etudiant, Professeur, User
from academics.models import Cours
from datetime import timezone
from django.utils import timezone

class Note(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumise', 'Soumise pour validation'),
        ('publiée', 'Publiée (visible étudiant)'),
        ('rejetée', 'Rejetée'),
    ]
    
    TYPE_EVALUATION = [
        ('examen', 'Examen'),
        ('tp', 'Travail Pratique'),
        ('projet', 'Projet'),
        ('partiel', 'Partiel'),
    ]
    
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, verbose_name="Étudiant")
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, verbose_name="Cours")
    valeur = models.FloatField(verbose_name="Note", help_text="Note sur 100")
    type_evaluation = models.CharField(max_length=20, choices=TYPE_EVALUATION, default='examen')
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='brouillon')
    
    # ✅ NOUVEAU : Motif de rejet
    motif_rejet = models.TextField(blank=True, null=True, verbose_name="Motif du rejet")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_soumission = models.DateTimeField(blank=True, null=True)  # ✅ NOUVEAU
    date_validation = models.DateTimeField(blank=True, null=True)  # ✅ NOUVEAU
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': User.Role.PROFESSEUR},
        null=True,
        blank=True,
        verbose_name="Professeur"
    )
    
    class Meta:
        verbose_name_plural = "Notes"
        unique_together = ['etudiant', 'cours', 'type_evaluation']
        ordering = ['cours', 'etudiant']
    
    def __str__(self):
        return f"{self.etudiant} - {self.cours}: {self.valeur}/100"
    
    def est_valide(self):
        """Valide que la note est entre 0 et 100"""
        return 0 <= self.valeur <= 100
    
    def get_statut_display_color(self):
        """Retourne la couleur Bootstrap selon le statut"""
        colors = {
            'brouillon': 'secondary',
            'soumise': 'warning', 
            'publiée': 'success',
            'rejetée': 'danger'
        }
        return colors.get(self.statut, 'secondary')
    
    # ✅ NOUVEAU : Méthodes de workflow
    def peut_modifier_par(self, user):
        """Vérifie si l'utilisateur peut modifier cette note"""
        if user.role == User.Role.PROFESSEUR:
            return (self.created_by == user and 
                   self.statut in ['brouillon', 'rejetée'])
        return False
    
    def soumettre(self):
        """Soumet la note pour validation"""
        if self.statut == 'brouillon':
            self.statut = 'soumise'
            self.date_soumission = timezone.now()
            self.save()
    
    def publier(self):
        """Publie la note (validation admin)"""
        if self.statut == 'soumise':
            self.statut = 'publiée'
            self.date_validation = timezone.now()
            self.motif_rejet = None  # Reset le motif si précédemment rejetée
            self.save()
    
    def rejeter(self, motif):
        """Rejette la note avec motif"""
        if self.statut == 'soumise':
            self.statut = 'rejetée'
            self.motif_rejet = motif
            self.save()
    
    @property
    def est_modifiable(self):
        """Vérifie si la note est modifiable (pour usage template)"""
        return self.statut in ['brouillon', 'rejetée']
    
    def peut_modifier_par(self, user):
        """Vérifie si l'utilisateur peut modifier cette note"""
        if user.role == User.Role.PROFESSEUR:
            return (self.created_by == user and 
                   self.statut in ['brouillon', 'rejetée'])
        return False
    

class MoyenneSemestre(models.Model):
    """Moyenne par semestre pour un étudiant"""
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE)
    semestre = models.CharField(max_length=10, choices=[('S1', 'Semestre 1'), ('S2', 'Semestre 2')])
    annee_academique = models.CharField(max_length=9, default='2025-2026')
    moyenne = models.FloatField()
    date_calcul = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['etudiant', 'semestre', 'annee_academique']
    
    def __str__(self):
        return f"{self.etudiant} - {self.semestre} {self.annee_academique}: {self.moyenne:.2f}"
    


class InscriptionCours(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='inscriptions')
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='inscriptions')
    date_inscription = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ['etudiant', 'cours']
        verbose_name = "Inscription à un cours"
        verbose_name_plural = "Inscriptions aux cours"

    def __str__(self):
        return f"{self.etudiant} → {self.cours}"

    