STATUT_BROUILLON = 'brouillon'
STATUT_SOUMISE = 'soumise'
STATUT_PUBLIEE = 'publiée'
STATUT_REJETEE = 'rejetée'

STATUTS_MODIFIABLES = [STATUT_BROUILLON, STATUT_REJETEE]

# grades/utils.py - CRÉER ce fichier
from academics.models import Cours
from grades.models import InscriptionCours
from django.utils import timezone

def reattribuer_cours_etudiant(etudiant):
    """
    Réattribue les cours à un étudiant selon son niveau/semestre
    UTILISE VOS MODÈLES EXISTANTS SANS LES MODIFIER
    """
    try:
        print(f"📚 Réattribution cours pour {etudiant.matricule}")
        
        # 1. Supprimer les anciennes inscriptions (VOTRE MODÈLE EXISTANT)
        supprimes = InscriptionCours.objects.filter(etudiant=etudiant).delete()
        print(f"   🗑️ {supprimes[0]} anciens cours supprimés")
        
        # 2. Trouver les nouveaux cours (VOTRE MODÈLE EXISTANT)
        nouveaux_cours = Cours.objects.filter(
            faculte=etudiant.faculte,
            niveau=etudiant.niveau,
            semestre=etudiant.semestre_courant
        )
        
        # 3. Créer les nouvelles inscriptions (VOTRE MODÈLE EXISTANT)
        for cours in nouveaux_cours:
            InscriptionCours.objects.get_or_create(
                etudiant=etudiant,
                cours=cours
            )
        
        print(f"   ✅ {nouveaux_cours.count()} nouveaux cours attribués")
        return True
        
    except Exception as e:
        print(f"❌ Erreur réattribution: {e}")
        return False


def calculer_et_stocker_moyennes(etudiant):
    """
    Calcule et stocke les moyennes d'un étudiant
    UTILISE VOS MODÈLES EXISTANTS
    """
    from grades.models import Note, MoyenneSemestre
    
    annee_courante = f"{timezone.now().year}-{timezone.now().year+1}"
    
    # Pour chaque semestre
    for semestre in ['S1', 'S2']:
        notes = Note.objects.filter(
            etudiant=etudiant,
            cours__semestre=semestre,
            statut='publiée'
        )
        
        if notes.exists():
            total = sum(float(note.valeur) for note in notes)
            moyenne = round(total / notes.count(), 2)
            
            # Stocker dans MoyenneSemestre (VOTRE MODÈLE EXISTANT)
            MoyenneSemestre.objects.update_or_create(
                etudiant=etudiant,
                semestre=semestre,
                annee_academique=annee_courante,
                defaults={'moyenne': moyenne}
            )
            
            print(f"   📊 {semestre}: {moyenne}/100 ({notes.count()} notes)")
    
    # Calculer et stocker la moyenne générale
    moyenne_gen = etudiant.calculer_moyenne_generale()
    if moyenne_gen:
        etudiant.moyenne_generale = round(moyenne_gen, 2)
        etudiant.save()
        print(f"   🎯 Moyenne générale: {etudiant.moyenne_generale}/100")

        