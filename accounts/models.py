from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        AUCUN = "", _("Aucun rôle")  # ✅ Ajout d'un choix vide
        ADMIN = "admin", _("Administrateur")
        PROFESSEUR = "prof", _("Professeur")
        ETUDIANT = "student", _("Étudiant")

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.AUCUN,  # ✅ Rôle vide par défaut
        blank=True
    )
    telephone = models.CharField(max_length=20, blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    first_login = models.BooleanField(default=True)

    def set_password(self, raw_password):
        super().set_password(raw_password)
        # Quand l'admin change le mot de passe, on marque first_login=True
        if self.pk and hasattr(self, '_password_changed_by_admin'):
            self.first_login = True
            self.save()


    def __str__(self):
        if self.role:
            return f"{self.username} ({self.get_role_display()})"
        return f"{self.username} (Aucun rôle)"  # ✅ Affichage si rôle vide


class Professeur(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialite = models.CharField(max_length=100)
    date_embauche = models.DateField()
    statut = models.CharField(max_length=20, choices=[('Permanent', 'Permanent'), ('Vacataire', 'Vacataire')])

    def __str__(self):
        return f"Prof. {self.user.get_full_name()}"


class Etudiant(models.Model):
    # CORRECTION : Ajout des choix pour le niveau
    NIVEAU_CHOICES = [
        ('1ere', '1ère année'),
        ('2e', '2e année'), 
        ('3e', '3e année'),
        ('4e', '4e année'),
        ('5e', '5e année'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    matricule = models.CharField(max_length=20, unique=True)
    faculte = models.ForeignKey('academics.Faculte', on_delete=models.CASCADE)
    # CORRECTION : Utilisation des choix pour le niveau
    niveau = models.CharField(max_length=10, choices=NIVEAU_CHOICES, default='1ere')
    date_inscription = models.DateField(auto_now_add=True)
    adresse = models.CharField(max_length=200)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    telephone_parent = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.matricule} - {self.user.get_full_name()}"
    
    
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_nomination = models.DateField(auto_now_add=True)
    niveau_acces = models.CharField(
        max_length=20,
        choices=[
            ('super', 'Super Administrateur'),
            ('academique', 'Administrateur Académique'),
            ('utilisateurs', 'Gestionnaire Utilisateurs')
        ],
        default='utilisateurs'
    )
    # Permissions granulaires
    peut_gerer_utilisateurs = models.BooleanField(default=True)
    peut_gerer_cours = models.BooleanField(default=True)
    peut_valider_notes = models.BooleanField(default=True)
    peut_gerer_facultes = models.BooleanField(default=True)
    
    def has_perm(self, permission_code):
        permissions = {
            'users.create': self.peut_gerer_utilisateurs,
            'users.delete': self.peut_gerer_utilisateurs,
            'courses.manage': self.peut_gerer_cours,
            'grades.validate': self.peut_valider_notes,
            'faculties.manage': self.peut_gerer_facultes,
        }
        return permissions.get(permission_code, False)
    
    
    def __str__(self):
        return f"Admin {self.user.get_full_name()}"

