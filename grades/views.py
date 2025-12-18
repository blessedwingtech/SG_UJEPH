from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Avg, Max

from accounts.views import is_admin
from grades.utils import STATUT_BROUILLON, STATUT_PUBLIEE, STATUT_REJETEE, STATUT_SOUMISE, STATUTS_MODIFIABLES
from .models import Note, MoyenneSemestre
from academics.models import Cours
from accounts.models import Etudiant, User

# Dans grades/views.py - MODIFIER saisie_notes
from django.utils import timezone
 
    
# @login_required
# def saisie_notes(request, cours_id):
#     """Professeur: Saisie des notes pour un cours avec restrictions intelligentes"""
#     if request.user.role != User.Role.PROFESSEUR:
#         messages.error(request, "Accès réservé aux professeurs")
#         return redirect('accounts:dashboard')
    
#     cours = get_object_or_404(Cours, id=cours_id, professeur=request.user)
#     etudiants = cours.etudiants_concernes().select_related('user')
    
#     # Récupérer toutes les notes existantes pour ce cours
#     notes_existantes = Note.objects.filter(
#         cours=cours, 
#         created_by=request.user
#     ).select_related('etudiant')
    
#     notes_dict = {note.etudiant_id: note for note in notes_existantes}
    
#     # ✅ ANALYSE DES STATUTS POUR LES RESTRICTIONS
#     notes_soumises = notes_existantes.filter(statut='soumise').exists()
#     notes_publiees = notes_existantes.filter(statut='publiée').exists()
#     notes_rejetees = notes_existantes.filter(statut='rejetée').exists()
#     notes_brouillon = notes_existantes.filter(statut='brouillon').exists()
    
#     # ✅ LOGIQUE DES RESTRICTIONS
#     peut_soumettre = not notes_soumises and (notes_brouillon or notes_rejetees)
#     peut_modifier_brouillons = not notes_soumises
#     toutes_notes_publiees = notes_publiees and not (notes_soumises or notes_brouillon or notes_rejetees)
    
#     if request.method == 'POST':
#         action = request.POST.get('action')
        
#         # ✅ VÉRIFICATION DES RESTRICTIONS
#         if action == 'soumettre' and not peut_soumettre:
#             messages.error(request, 
#                 "❌ Impossible de soumettre : certaines notes sont déjà en attente de validation "
#                 "ou aucune note n'est prête à être soumise."
#             )
#             return redirect('grades:saisie_notes', cours_id=cours_id)
        
#         if action == 'enregistrer' and not peut_modifier_brouillons:
#             messages.error(request, 
#                 "❌ Impossible de modifier : des notes sont en attente de validation. "
#                 "Veuillez attendre la validation de l'admin ou annuler la soumission."
#             )
#             return redirect('grades:saisie_notes', cours_id=cours_id)
        
#         # Traitement des notes
#         for etudiant in etudiants:
#             note_value = request.POST.get(f'note_{etudiant.id}')
            
#             if not note_value:
#                 continue
                
#             try:
#                 note_value = float(note_value)
#                 if not (0 <= note_value <= 100):
#                     messages.error(request, f"Note invalide pour {etudiant.user.get_full_name()}")
#                     continue
#             except (ValueError, TypeError):
#                 messages.error(request, f"Format de note invalide pour {etudiant.user.get_full_name()}")
#                 continue
            
#             # Déterminer le statut selon l'action et les restrictions
#             if action == 'soumettre' and peut_soumettre:
#                 nouveau_statut = 'soumise'
#             elif action == 'enregistrer' and peut_modifier_brouillons:
#                 nouveau_statut = 'brouillon'
#             else:
#                 continue  # Ne pas traiter si restriction activée
            
#             note, created = Note.objects.get_or_create(
#                 etudiant=etudiant,
#                 cours=cours,
#                 type_evaluation='examen',
#                 defaults={
#                     'valeur': note_value,
#                     'created_by': request.user,
#                     'statut': nouveau_statut
#                 }
#             )
            
#             if not created:
#                 # Vérifier si la note peut être modifiée
#                 if not note.peut_modifier_par(request.user):
#                     messages.error(request, 
#                         f"Note de {etudiant.user.get_full_name()} non modifiable "
#                         f"(statut: {note.get_statut_display()})"
#                     )
#                     continue
                
#                 # Mettre à jour la note
#                 note.valeur = note_value
#                 note.statut = nouveau_statut
                
#                 if action == 'soumettre':
#                     note.date_soumission = timezone.now()
#                     note.motif_rejet = None  # Reset le motif si re-soumission
                
#                 note.save()
        
#         # Messages de confirmation
#         if action == 'soumettre':
#             messages.success(request, 
#                 "✅ Notes soumises pour validation avec succès! "
#                 "Vous ne pourrez plus les modifier avant la validation de l'admin."
#             )
#         elif action == 'enregistrer':
#             messages.success(request, "💾 Notes enregistrées en brouillon!")
        
#         return redirect('grades:saisie_notes', cours_id=cours_id)
    
#     context = {
#         'cours': cours,
#         'etudiants': etudiants,
#         'notes_dict': notes_dict,
#         # ✅ NOUVEAUX CONTEXTES POUR LES RESTRICTIONS
#         'notes_soumises': notes_soumises,
#         'notes_publiees': notes_publiees,
#         'notes_rejetees': notes_rejetees,
#         'notes_brouillon': notes_brouillon,
#         'peut_soumettre': peut_soumettre,
#         'peut_modifier_brouillons': peut_modifier_brouillons,
#         'toutes_notes_publiees': toutes_notes_publiees,
#     }
#     return render(request, 'grades/saisie_notes.html', context)

 

@login_required
def saisie_notes(request, cours_id):
    """
    Vue pour la saisie des notes avec validation par bloc
    """
    if request.user.role != User.Role.PROFESSEUR:
        messages.error(request, "❌ Accès réservé aux professeurs")
        return redirect('accounts:dashboard')

    # Récupérer le cours
    cours = get_object_or_404(Cours, id=cours_id, professeur=request.user)
    
    # Récupérer les étudiants
    
    #etudiants = cours.etudiants_concernes().select_related('user')
    etudiants = Etudiant.objects.filter(
            inscriptions__cours=cours
        ).select_related('user').distinct()
    
    # Récupérer les notes existantes
    notes = Note.objects.filter(
        cours=cours,
        created_by=request.user
    ).select_related('etudiant')
    
    notes_dict = {n.etudiant_id: n for n in notes}
    
    # ANALYSE DES STATUTS
    aucune_note = not notes.exists()
    
    # Vérifier les différents statuts présents
    statuts_presents = set(notes.values_list('statut', flat=True))
    
    # Variables pour le template
    notes_soumises = STATUT_SOUMISE in statuts_presents
    notes_publiees = STATUT_PUBLIEE in statuts_presents
    notes_rejetees = STATUT_REJETEE in statuts_presents
    notes_brouillon = STATUT_BROUILLON in statuts_presents
    
    # Vérifier si tous les étudiants ont une note
    tous_ont_note = etudiants.count() == notes.count()
    
    # LOGIQUE DE PERMISSION CORRIGÉE
    # 1. Peut modifier si AUCUNE note n'est soumise ou publiée
    peut_modifier = not (notes_soumises or notes_publiees)
    
    # 2. Peut soumettre si :
    #    - On peut modifier (pas de notes soumises/publiées)
    #    - Tous les étudiants ont une note
    #    - Il y a au moins une note
    peut_soumettre = peut_modifier and tous_ont_note and notes.exists()
    
    # 3. Toutes notes publiées ?
    toutes_notes_publiees = (
        notes_publiees and 
        not notes_soumises and 
        not notes_rejetees and 
        not notes_brouillon and
        tous_ont_note
    )
    
    # TRAITEMENT DU FORMULAIRE POST - CORRECTION IMPORTANTE
    if request.method == 'POST':
        action = request.POST.get('action')
        
        print(f"Action reçue: {action}")  # DEBUG
        
        # VALIDATION DES PERMISSIONS
        if action == 'soumettre':
            if not peut_soumettre:
                if notes_soumises:
                    messages.error(request, 
                        "❌ IMPOSSIBLE DE SOUMETTRE : Les notes sont déjà soumises pour validation."
                    )
                elif notes_publiees:
                    messages.error(request, 
                        "❌ IMPOSSIBLE DE SOUMETTRE : Les notes sont déjà publiées."
                    )
                elif not tous_ont_note:
                    missing_count = etudiants.count() - notes.count()
                    messages.error(request, 
                        f"❌ IMPOSSIBLE DE SOUMETTRE : {missing_count} étudiant(s) sans note."
                    )
                return redirect('grades:saisie_notes', cours_id=cours_id)
        
        if action == 'enregistrer' and not peut_modifier:
            if notes_soumises:
                messages.error(request, "❌ IMPOSSIBLE DE MODIFIER : Notes en attente de validation.")
            elif notes_publiees:
                messages.error(request, "❌ IMPOSSIBLE DE MODIFIER : Notes déjà publiées.")
            return redirect('grades:saisie_notes', cours_id=cours_id)
        
        # Déterminer le nouveau statut
        nouveau_statut = STATUT_SOUMISE if action == 'soumettre' else STATUT_BROUILLON
        
        print(f"Nouveau statut: {nouveau_statut}")  # DEBUG
        
        notes_traitees = 0
        erreurs = []
        
        for etudiant in etudiants:
            valeur_str = request.POST.get(f'note_{etudiant.id}')
            
            # Si pas de valeur et qu'on soumet, c'est une erreur
            if action == 'soumettre' and not valeur_str:
                erreurs.append(f"{etudiant.user.get_full_name()}: Note manquante")
                continue
            
            # Si pas de valeur et enregistrement brouillon, on peut passer
            if action == 'enregistrer' and not valeur_str:
                continue
            
            # Validation de la valeur
            try:
                valeur = float(valeur_str)
                if not 0 <= valeur <= 100:
                    raise ValueError(f"Note invalide: {valeur}/100")
            except (ValueError, TypeError) as e:
                erreurs.append(f"{etudiant.user.get_full_name()}: {str(e)}")
                continue
            
            # CRÉATION/MISE À JOUR DE LA NOTE - CORRECTION CRITIQUE
            try:
                # Essayer de récupérer la note existante
                note = Note.objects.get(
                    etudiant=etudiant,
                    cours=cours,
                    type_evaluation='examen'
                )
                
                # Vérifier si on peut modifier cette note
                if note.statut in [STATUT_SOUMISE, STATUT_PUBLIEE]:
                    erreurs.append(f"{etudiant.user.get_full_name()}: Note non modifiable")
                    continue
                
                # Mettre à jour la note existante
                note.valeur = valeur
                note.statut = nouveau_statut
                note.motif_rejet = None  # Réinitialiser le motif
                
                if action == 'soumettre':
                    note.date_soumission = timezone.now()
                else:
                    note.date_soumission = None
                
                note.save()
                
            except Note.DoesNotExist:
                # Créer une nouvelle note
                note = Note.objects.create(
                    etudiant=etudiant,
                    cours=cours,
                    type_evaluation='examen',
                    valeur=valeur,
                    created_by=request.user,
                    statut=nouveau_statut,
                    motif_rejet=None,
                    date_soumission=timezone.now() if action == 'soumettre' else None
                )
            
            notes_traitees += 1
        
        # Afficher les messages d'erreur
        if erreurs:
            for erreur in erreurs[:3]:
                messages.error(request, erreur)
        
        # MESSAGES DE CONFIRMATION
        if notes_traitees > 0:
            if action == 'soumettre':
                # VÉRIFIER QUE LE STATUT EST BIEN SOUMIS
                notes_soumises_verif = Note.objects.filter(
                    cours=cours,
                    created_by=request.user,
                    statut=STATUT_SOUMISE
                ).count()
                
                messages.success(request, 
                    f"✅ {notes_traitees} NOTE(S) SOUMISE(S) AVEC SUCCÈS !"
                )
                messages.warning(request, 
                    f"Statut confirmé: {notes_soumises_verif} note(s) avec statut 'soumise'"
                )
            else:  # enregistrer
                messages.success(request, 
                    f"💾 {notes_traitees} NOTE(S) ENREGISTRÉE(S) EN BROUILLON"
                )
        
        return redirect('grades:saisie_notes', cours_id=cours_id)
    
    # Préparer le contexte
    context = {
        'cours': cours,
        'etudiants': etudiants,
        'notes_dict': notes_dict,
        'peut_modifier': peut_modifier,
        'peut_soumettre': peut_soumettre,
        'tous_ont_note': tous_ont_note,
        'aucune_note': aucune_note,
        'notes_soumises': notes_soumises,
        'toutes_notes_publiees': toutes_notes_publiees,
        'notes_rejetees': notes_rejetees,
        'notes_brouillon': notes_brouillon,
    }
    
    return render(request, 'grades/saisie_notes.html', context)

# @login_required
# @user_passes_test(is_admin)
# def validation_notes(request):
#     """Admin: Validation des notes soumises avec motif de rejet"""
#     if request.user.role != User.Role.ADMIN:
#         messages.error(request, "Accès réservé aux administrateurs")
#         return redirect('accounts:dashboard')
    
#     notes_soumises = Note.objects.filter(statut='soumise').select_related(
#         'cours', 'etudiant__user', 'created_by'
#     )
    
#     if request.method == 'POST':
#         note_id = request.POST.get('note_id')
#         action = request.POST.get('action')
#         motif_rejet = request.POST.get('motif_rejet', '').strip()
        
#         if note_id and action:
#             try:
#                 note = Note.objects.get(id=note_id, statut='soumise')
                
#                 if action == 'publier':
#                     note.publier()
#                     messages.success(request, 
#                         f"✅ Note de {note.etudiant.user.get_full_name()} publiée avec succès!"
#                     )
                    
#                 elif action == 'rejeter':
#                     if not motif_rejet:
#                         messages.error(request, 
#                             "❌ Veuillez fournir un motif de rejet."
#                         )
#                         return redirect('grades:validation_notes')
                    
#                     note.rejeter(motif_rejet)
#                     messages.warning(request, 
#                         f"❌ Note de {note.etudiant.user.get_full_name()} rejetée. "
#                         f"Motif: {motif_rejet}"
#                     )
                    
#             except Note.DoesNotExist:
#                 messages.error(request, "❌ Note non trouvée ou déjà traitée")
        
#         return redirect('grades:validation_notes')
    
#     context = {
#         'notes_soumises': notes_soumises,
#     }
#     return render(request, 'grades/validation_notes.html', context)

 

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db.models import Count, Q
from .models import Cours, Note, User

# Définir ces constantes quelque part (par exemple dans un fichier constants.py)
STATUT_BROUILLON = 'brouillon'
STATUT_SOUMISE = 'soumise'
STATUT_PUBLIEE = 'publiée'
STATUT_REJETEE = 'rejetée'

def is_admin(user):
    return user.role == User.Role.ADMIN

@login_required
@user_passes_test(is_admin)
def validation_notes(request):
    """
    Admin: Liste des cours avec notes soumises
    """
    if request.user.role != User.Role.ADMIN:
        messages.error(request, "❌ Accès réservé aux administrateurs")
        return redirect('accounts:dashboard')
    
    # Récupérer les cours qui ont des notes soumises
    cours_ids = Note.objects.filter(
        statut=STATUT_SOUMISE
    ).values_list('cours_id', flat=True).distinct()
    
    # Annoter avec le nombre de notes soumises
    cours_list = Cours.objects.filter(id__in=cours_ids).annotate(
        notes_soumises_count=Count('note', filter=Q(note__statut=STATUT_SOUMISE))
    ).select_related('professeur', 'faculte')
    
    # Ajouter la date de dernière soumission pour chaque cours
    for cours in cours_list:
        derniere_note = cours.note_set.filter(
            statut=STATUT_SOUMISE
        ).order_by('-date_soumission').first()
        cours.date_derniere_soumission = derniere_note.date_soumission if derniere_note else None
    
    context = {
        'cours_soumis': cours_list,
    }
    return render(request, 'grades/validation_notes.html', context)

@login_required
@user_passes_test(is_admin)
def traiter_cours_notes(request, cours_id):
    """
    Admin: Traiter toutes les notes d'un cours (version améliorée)
    """
    if request.user.role != User.Role.ADMIN:
        messages.error(request, "❌ Accès réservé aux administrateurs")
        return redirect('accounts:dashboard')
    
    cours = get_object_or_404(Cours, id=cours_id)
    
    # Récupérer uniquement les notes soumises
    notes = Note.objects.filter(
        cours=cours,
        statut=STATUT_SOUMISE
    ).select_related('etudiant__user')
    
    if not notes.exists():
        messages.error(request, "❌ Ce cours n'a pas de notes en attente de validation.")
        return redirect('grades:validation_notes')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        motif = request.POST.get('motif_rejet', '').strip()
        
        if action == 'publier':
            # Publier toutes les notes
            notes.update(
                statut=STATUT_PUBLIEE,
                date_validation=timezone.now()
            )
            
            messages.success(request, 
                f"✅ {notes.count()} NOTE(S) PUBLIÉE(S) !\n"
                f"Les notes du cours '{cours.intitule}' sont maintenant visibles par les étudiants."
            )
            
        elif action == 'rejeter':
            if not motif:
                messages.error(request, "❌ Vous devez fournir un motif de rejet.")
                return redirect('grades:traiter_cours_notes', cours_id=cours_id)
            
            # Rejeter toutes les notes avec le même motif
            notes.update(
                statut=STATUT_REJETEE,
                motif_rejet=motif
            )
            
            messages.warning(request, 
                f"❌ {notes.count()} NOTE(S) REJETÉE(S)\n"
                f"Motif: {motif}"
            )
        
        return redirect('grades:validation_notes')
    
    context = {
        'cours': cours,
        'notes': notes,
    }
    return render(request, 'grades/traiter_cours.html', context)



@login_required
def consulter_notes_etudiant(request):
    """Étudiant: Consultation de ses notes publiées"""
    if request.user.role != User.Role.ETUDIANT or not hasattr(request.user, 'etudiant'):
        messages.error(request, "❌ Accès réservé aux étudiants")
        return redirect('accounts:dashboard')
    
    etudiant = request.user.etudiant
    
    # Récupérer les notes publiées
    notes_publiees = Note.objects.filter(
        etudiant=etudiant,
        statut='publiée'
    ).select_related(
        'cours', 
        'cours__faculte',
        'created_by'
    ).order_by(
        'cours__semestre', 
        'cours__intitule'
    )
    
    # Calcul des moyennes par semestre (avec vos champs existants)
    moyenne_s1 = None
    moyenne_s2 = None
    
    # Pour S1
    # Calcul des moyennes par semestre (CORRECTION)  
    notes_s1 = notes_publiees.filter(cours__semestre='S1')
    if notes_s1.exists():
        # ✅ CORRECTION : Calcul simple (plus de crédits)
        total_s1 = sum(float(note.valeur) for note in notes_s1)
        moyenne_s1 = total_s1 / notes_s1.count()  # Moyenne arithmétique simple
    else:
        moyenne_s1 = None

    # Pour S2
    notes_s2 = notes_publiees.filter(cours__semestre='S2')
    if notes_s2.exists():
        # ✅ CORRECTION : Calcul simple (plus de crédits)
        total_s2 = sum(float(note.valeur) for note in notes_s2)
        moyenne_s2 = total_s2 / notes_s2.count()  # Moyenne arithmétique simple
    else:
        moyenne_s2 = None

    # Calcul de la moyenne générale (seulement si S2 disponible)
    moyenne_generale = None
    if moyenne_s1 is not None and moyenne_s2 is not None:
        moyenne_generale = (moyenne_s1 + moyenne_s2) / 2
    elif moyenne_s2 is not None:
        moyenne_generale = moyenne_s2  # Seul S2 disponible
    
    # Compter les notes par semestre
    count_s1 = notes_s1.count()
    count_s2 = notes_s2.count()
    
    context = {
        'etudiant': etudiant,
        'notes_publiees': notes_publiees,
        'moyenne_s1': moyenne_s1,
        'moyenne_s2': moyenne_s2,
        'moyenne_generale': moyenne_generale,
        'count_s1': count_s1,
        'count_s2': count_s2,
        'total_notes': notes_publiees.count(),
    }
    return render(request, 'grades/consulter_notes_etudiant.html', context)
