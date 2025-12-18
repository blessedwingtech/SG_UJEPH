from django.utils import timezone
from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import UserEditForm, UserForm, EtudiantForm, ProfesseurForm
from .models import User, Etudiant, Professeur, Admin  # ✅ Admin importé
from django.core.paginator import Paginator   
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.views.decorators.http import require_http_methods
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST 
import json
import re
import secrets
import string 
from django.db import IntegrityError, transaction
from django.db.models import signals 
from .signals import create_user_profile 
 
from django.contrib import messages
from .forms import UserProfileForm 
from django.core.exceptions import ObjectDoesNotExist
 
from academics.models import Faculte 
from academics.models import Cours, Annonce 
 
from django.http import HttpResponse
from django.db.models import Q
import csv
import io 



User = get_user_model()
def is_admin(user):
    return (
        user.is_authenticated and
        user.role == User.Role.ADMIN and
        hasattr(user, 'admin')
    )


def can_manage_users(user):
    return is_admin(user) and user.admin.peut_gerer_utilisateurs

def can_validate_grades(user):
    return is_admin(user) and user.admin.peut_valider_notes

def can_manage_facultes(user):
    return is_admin(user) and user.admin.peut_gerer_facultes

def can_manage_cours(user):
    return is_admin(user) and user.admin.peut_gerer_cours


# Ajoutez cette fonction dans academics/views.py
def get_annonces_accueil(request):
    """Récupère les annonces à afficher sur la page d'accueil"""
    from django.utils import timezone
    from academics.models import Annonce
    
    now = timezone.now()
    
    # Annonces actives (publiées et non expirées)
    annonces = Annonce.objects.filter(
        est_publie=True,
        date_publication__lte=now
    ).exclude(
        date_expiration__lt=now
    ).order_by('-est_important', '-priorite', '-date_publication')
    
    # Filtrer par destinataire si l'utilisateur est connecté
    if request.user.is_authenticated:
        if request.user.role == 'student':
            annonces = annonces.filter(
                destinataire_tous=True
            ) | annonces.filter(
                destinataire_etudiants=True
            )
        elif request.user.role == 'prof':
            annonces = annonces.filter(
                destinataire_tous=True
            ) | annonces.filter(
                destinataire_professeurs=True
            )
        elif request.user.role == 'admin':
            annonces = annonces.filter(
                destinataire_tous=True
            ) | annonces.filter(
                destinataire_admins=True
            )
    else:
        # Pour les visiteurs non connectés, uniquement les annonces "pour tous"
        annonces = annonces.filter(destinataire_tous=True)
    
    return annonces.distinct()[:10]  # Limiter à 10 annonces

def home(request):
    """Page d'accueil"""
    from academics.views import get_annonces_accueil
    from academics.models import Faculte
    from accounts.models import User
    
    # Récupérer les annonces actives
    annonces = get_annonces_accueil(request)
    
    # Récupérer toutes les facultés
    facultes = Faculte.objects.all()[:6]  # Limiter à 6 pour l'affichage
    
    # Statistiques (vous pouvez les remplacer par vos vraies données)
    context = {
        'annonces': annonces,
        'facultes': facultes,
        'total_etudiants': User.objects.filter(role='student').count(),
        'total_professeurs': User.objects.filter(role='prof').count(),
        'total_facultes': Faculte.objects.count(),
        'total_cours': Cours.objects.count() if 'Cours' in globals() else 85,
    }
    return render(request, 'home.html', context)



 
User = get_user_model()

from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json, re
from .models import User

@require_POST
def check_username(request):
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()

        if not username:
            return JsonResponse({
                'exists': False,
                'valid': False,
                'message': 'Nom d\'utilisateur vide'
            })

        # Format correct : lettre ou underscore au début
        if not re.match(r'^[a-zA-Z_].*$', username):
            return JsonResponse({
                'exists': False,
                'valid': False,
                'message': 'Le nom doit commencer par une lettre ou underscore'
            })

        # Longueur minimale
        if len(username) < 3:
            return JsonResponse({
                'exists': False,
                'valid': False,
                'message': 'Minimum 3 caractères'
            })

        # Vérifier existence
        exists = User.objects.filter(username=username).exists()

        return JsonResponse({
            'exists': exists,
            'valid': True,
            'message': 'Nom déjà pris' if exists else 'Nom disponible'
        })

    except Exception as e:
        return JsonResponse({
            'exists': False,
            'valid': False,
            'message': f'Erreur serveur : {str(e)}'
        }, status=500)

# @require_POST
# def check_username(request):
#     """Vérifie si un nom d'utilisateur existe et valide le format"""
#     try:
#         data = json.loads(request.body)
#         username = data.get('username', '').strip()
        
#         if not username:
#             return JsonResponse({
#                 'exists': False,
#                 'valid': False,
#                 'message': 'Nom d\'utilisateur vide'
#             })
        
#         # Validation du format (lettre ou underscore au début)
#         is_valid_format = bool(re.match(r'^[a-zA-Z_].*$', username))
        
#         if not is_valid_format:
#             return JsonResponse({
#                 'exists': False,
#                 'valid': False,
#                 'message': 'Le nom d\'utilisateur doit commencer par une lettre ou underscore'
#             })
        
#         # Vérifier la longueur minimale
#         if len(username) < 3:
#             return JsonResponse({
#                 'exists': False,
#                 'valid': False,
#                 'message': 'Le nom d\'utilisateur doit contenir au moins 3 caractères'
#             })
        
#         # Vérifier si l'utilisateur existe
#         exists = User.objects.filter(username=username).exists()
        
#         return JsonResponse({
#             'exists': exists,
#             'valid': True,
#             'username': username,
#             'message': 'Utilisateur trouvé' if exists else 'Utilisateur non reconnu'
#         })
        
#     except json.JSONDecodeError:
#         return JsonResponse({
#             'error': 'Invalid JSON format',
#             'valid': False,
#             'exists': False
#         }, status=400)
#     except Exception as e:
#         return JsonResponse({
#             'error': str(e),
#             'valid': False,
#             'exists': False
#         }, status=500)
    

def login_view(request):
    """Vue de connexion avec validation en temps réel"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Validation basique
        if not username or not password:
            return render(request, 'login.html', {
                'error': 'Veuillez remplir tous les champs',
                'form': {
                    'username': {'value': username or ''},
                    'password': {'value': ''}
                }
            })
        
        # Tentative d'authentification
        user = authenticate(request, username=username, password=password)
        
        if user:
            if user.is_active:
                login(request, user)
                
                # Vérifier si premier login
                if hasattr(user, 'first_login') and user.first_login:
                    messages.info(request, "Veuillez changer votre mot de passe pour la première connexion.")
                    return redirect('accounts:change_password_required')
                
                # Redirection vers le dashboard
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('accounts:dashboard')
            else:
                return render(request, 'login.html', {
                    'error': 'Ce compte est désactivé',
                    'form': {
                        'username': {'value': username},
                        'password': {'value': ''}
                    }
                })
        else:
            return render(request, 'login.html', {
                'error': 'Nom d\'utilisateur ou mot de passe incorrect',
                'form': {
                    'username': {'value': username},
                    'password': {'value': ''}
                }
            })
    
    # GET request - afficher le formulaire vide
    return render(request, 'login.html', {
        'form': {
            'username': {'value': ''},
            'password': {'value': ''}
        }
    })


@login_required
def change_password_required(request):
    if not request.user.first_login:
        return redirect('accounts:dashboard')
        
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.first_login = False
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Mot de passe changé avec succès!")
            return redirect('accounts:dashboard')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password_required.html', {'form': form})

@require_http_methods(["POST"])
@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def logout_confirm(request):
    return render(request, 'accounts/logout_confirm.html')

# ✅ CORRECTION : AJOUTER LA CRÉATION D'ADMIN
@login_required
@user_passes_test(is_admin)
def creer_admin(request):
    """Créer un nouvel administrateur"""
    # DÉSACTIVER le signal pour éviter les doublons
    post_save.disconnect(create_user_profile, sender=User)
    
    try:
        if request.method == 'POST':
            user_form = UserForm(request.POST)
            if user_form.is_valid():
                try:
                    user = user_form.save(commit=False)
                    user.role = User.Role.ADMIN
                    user.first_login = True
                    
                    # ✅ MOT DE PASSE PAR DÉFAUT (comme pour étudiant)
                    user.set_password("1234")  # Mot de passe par défaut
                    user.save()
                    
                    # ✅ CRÉER LE PROFIL ADMIN
                    Admin.objects.create(
                        user=user,
                        niveau_acces='utilisateurs',
                        peut_gerer_utilisateurs=True,
                        peut_gerer_cours=True,
                        peut_valider_notes=True,
                        peut_gerer_facultes=True
                    )
                    
                    messages.success(request, "Administrateur créé avec succès")
                    messages.info(request, "Mot de passe par défaut : 1234")
                    
                    # Réactiver le signal avant redirection
                    post_save.connect(create_user_profile, sender=User)
                    return redirect('accounts:dashboard')
                    
                except IntegrityError as e:
                    messages.error(request, f"Erreur lors de la création : {e}")
                    if user.pk:
                        user.delete()
            else:
                messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
        else:
            user_form = UserForm()
    
    except Exception as e:
        messages.error(request, f"Erreur système : {str(e)}")
    
    finally:
        # TOUJOURS réactiver le signal
        try:
            post_save.connect(create_user_profile, sender=User)
        except:
            pass

    return render(request, 'accounts/creer_admin.html', {'user_form': user_form})

 
from django.db import IntegrityError 

User = get_user_model()

# @login_required
# @user_passes_test(can_manage_users)
# def creer_etudiant(request):
#     # Créer les formulaires sans les champs password et confirm_password
#     user_form = UserForm(request.POST or None)
#     etu_form = EtudiantForm(request.POST or None)

#     if request.method == 'POST':
#         if user_form.is_valid() and etu_form.is_valid():
#             try:
#                 # Créer l'utilisateur
#                 user = user_form.save(commit=False)
#                 user.role = User.Role.ETUDIANT
#                 user.first_login = True
                
#                 # Mot de passe fixe "1234"
#                 user.set_password("1234")
#                 user.save()

#                 # Créer l'étudiant avec matricule automatique
#                 etudiant = etu_form.save(commit=False)
#                 etudiant.user = user
                
#                 # Générer le matricule
#                 annee = timezone.now().year
#                 faculte_code = etudiant.faculte.code[:3].upper() if etudiant.faculte.code else "ETU"
                
#                 # Trouver le dernier numéro pour cette faculté et année
#                 dernier = Etudiant.objects.filter(
#                     matricule__startswith=f"{annee}-{faculte_code}-"
#                 ).order_by('-matricule').first()
                
#                 if dernier:
#                     dernier_num = int(dernier.matricule.split('-')[-1])
#                     nouveau_num = dernier_num + 1
#                 else:
#                     nouveau_num = 1
                
#                 etudiant.matricule = f"{annee}-{faculte_code}-{nouveau_num:04d}"
#                 etudiant.save()

#                 # Message de succès avec Toast
#                 messages.success(request, f"Étudiant {user.get_full_name()} créé avec succès !")
                
#                 # Rediriger vers la liste
#                 return redirect('accounts:liste_etudiants')

#             except IntegrityError as e:
#                 messages.error(request, f"Erreur lors de la création : {str(e)}")
#                 if user.pk:
#                     user.delete()
#             except Exception as e:
#                 messages.error(request, f"Erreur inattendue : {str(e)}")
#         else:
#             messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")

#     return render(request, 'accounts/creer_etudiant.html', {
#         'user_form': user_form,
#         'etu_form': etu_form,
#         'form_invalid': request.method == 'POST'
#     })

from django.db import transaction
from django.db.models.signals import post_save
 
 

@login_required
@user_passes_test(can_manage_users)
def creer_etudiant(request):
    # DÉSACTIVER le signal au tout début
    post_save.disconnect(create_user_profile, sender=User)
    
    user_form = UserForm(request.POST or None)
    etu_form = EtudiantForm(request.POST or None)
    
    try:
        if request.method == 'POST':
            # Debug simplifié
            print(f"=== CRÉATION ÉTUDIANT ===")
            print(f"Forms valides: User={user_form.is_valid()}, Etu={etu_form.is_valid()}")
            
            if user_form.is_valid() and etu_form.is_valid():
                try:
                    # Vérifications préliminaires
                    username = user_form.cleaned_data['username']
                    email = user_form.cleaned_data['email']
                    
                    if User.objects.filter(username=username).exists():
                        messages.error(request, f"Le nom d'utilisateur '{username}' est déjà utilisé.")
                        return render(request, 'accounts/creer_etudiant.html', {
                            'user_form': user_form,
                            'etu_form': etu_form,
                            'form_invalid': True
                        })
                    
                    if User.objects.filter(email=email).exists():
                        messages.error(request, f"L'email '{email}' est déjà utilisé.")
                        return render(request, 'accounts/creer_etudiant.html', {
                            'user_form': user_form,
                            'etu_form': etu_form,
                            'form_invalid': True
                        })
                    
                    # TRANSACTION ATOMIQUE - Tout ou rien
                    with transaction.atomic():
                        # 1. Créer l'utilisateur
                        user = user_form.save(commit=False)
                        user.role = User.Role.ETUDIANT
                        user.first_login = True
                        user.set_password("1234")
                        user.save()
                        print(f"✅ User créé: {user.username} (ID:{user.id})")
                        
                        # 2. Créer l'étudiant avec matricule
                        etudiant = etu_form.save(commit=False)
                        etudiant.user = user
                        
                        # Générer matricule unique
                        annee = timezone.now().year
                        faculte_code = etudiant.faculte.code[:3].upper() if etudiant.faculte.code else "ETU"
                        
                        # Trouver le prochain numéro
                        dernier = Etudiant.objects.filter(
                            matricule__startswith=f"{annee}-{faculte_code}-"
                        ).order_by('-matricule').first()
                        
                        if dernier:
                            try:
                                dernier_num = int(dernier.matricule.split('-')[-1])
                                nouveau_num = dernier_num + 1
                            except (ValueError, IndexError):
                                nouveau_num = 1
                        else:
                            nouveau_num = 1
                        
                        etudiant.matricule = f"{annee}-{faculte_code}-{nouveau_num:04d}"
                        etudiant.save()
                        print(f"✅ Étudiant créé: {etudiant.matricule}")
                        
                        # 3. Attribution des cours (si nécessaire)
                        try:
                            from grades.models import InscriptionCours
                            from academics.models import Cours
                            
                            mois = timezone.now().month
                            semestre = 'S1' if (9 <= mois <= 12 or mois == 1) else 'S2'
                            cours_disponibles = Cours.objects.filter(
                                faculte=etudiant.faculte,
                                niveau=etudiant.niveau,
                                semestre=semestre
                            )
                            
                            for cours in cours_disponibles:
                                InscriptionCours.objects.get_or_create(
                                    etudiant=etudiant,
                                    cours=cours
                                )
                            print(f"📚 {cours_disponibles.count()} cours attribués")
                        except Exception as e:
                            print(f"⚠️ Cours non attribués: {e}")
                    
                    # SUCCÈS - Réactiver le signal avant redirection
                    post_save.connect(create_user_profile, sender=User)
                    messages.success(request, f"✅ Étudiant {user.get_full_name()} créé avec succès !")
                    return redirect('accounts:liste_etudiants')
                    
                except Exception as e:
                    print(f"❌ Erreur création: {str(e)}")
                    messages.error(request, f"Erreur: {str(e)}")
            
            else:
                # Affichage des erreurs de formulaire
                if not user_form.is_valid():
                    for field, errors in user_form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
                
                if not etu_form.is_valid():
                    for field, errors in etu_form.errors.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
    
    except Exception as e:
        print(f"❌ Erreur globale: {str(e)}")
        messages.error(request, f"Erreur système: {str(e)}")
    
    finally:
        # TOUJOURS réactiver le signal, même en cas d'erreur
        try:
            # Vérifier si le signal n'est pas déjà connecté
            receivers = post_save._live_receivers(User)
            signal_connected = False
            
            for receiver in receivers:
                # Vérification sécurisée
                try:
                    if hasattr(receiver, '__name__') and receiver.__name__ == 'create_user_profile':
                        signal_connected = True
                        break
                except:
                    continue
            
            if not signal_connected:
                post_save.connect(create_user_profile, sender=User)
                print("✅ Signal réactivé")
        except Exception as e:
            print(f"⚠️ Erreur réactivation signal: {e}")
            # Tentative de réactivation malgré l'erreur
            try:
                post_save.connect(create_user_profile, sender=User)
            except:
                pass
    
    # Rendu du template (GET ou POST avec erreurs)
    return render(request, 'accounts/creer_etudiant.html', {
        'user_form': user_form,
        'etu_form': etu_form,
        'form_invalid': request.method == 'POST'
    })



@login_required
@user_passes_test(can_manage_users)
def creer_professeur(request):
    """
    Vue optimisée pour la création d'un professeur.
    Gestion robuste des transactions, signaux et erreurs.
    """
    user_form = UserForm(request.POST or None)
    prof_form = ProfesseurForm(request.POST or None)

    if request.method == 'POST':
        if user_form.is_valid() and prof_form.is_valid():
            try:
                # 🔒 DÉBUT DE LA TRANSACTION ATOMIQUE
                with transaction.atomic():
                    # 🔇 DÉSACTIVER TEMPORAIREMENT LE SIGNAL
                    signals.post_save.disconnect(create_user_profile, sender=User)
                    
                    # 👤 CRÉATION DE L'UTILISATEUR
                    user = user_form.save(commit=False)
                    user.role = User.Role.PROFESSEUR
                    user.first_login = True
                    
                    # 🔑 MOT DE PASSE PAR DÉFAUT (fixe)
                    user.set_password("1234")
                    user.save()
                    
                    # 👨‍🏫 CRÉATION DU PROFIL PROFESSEUR
                    professeur = prof_form.save(commit=False)
                    professeur.user = user
                    professeur.save()
                    
                    # 🔊 RÉACTIVER LE SIGNAL
                    signals.post_save.connect(create_user_profile, sender=User)
                
                # ✅ SUCCÈS - MESSAGE ET REDIRECTION
                full_name = user.get_full_name() or user.username
                messages.success(
                    request, 
                    f"✅ Professeur <strong>{full_name}</strong> créé avec succès ! "
                    f"(Matricule: {user.username}, Mot de passe: 1234)"
                )
                
                # 📊 LOG SUCCÈS (optionnel)
                print(f"✅ PROFESSEUR CRÉÉ: {user.username} ({user.email})")
                
                return redirect('accounts:liste_professeurs')

            except IntegrityError as e:
                # 🔄 RÉACTIVER LE SIGNAL EN CAS D'ERREUR
                signals.post_save.connect(create_user_profile, sender=User)
                
                # 🚨 GESTION DES ERREURS D'INTÉGRITÉ SPÉCIFIQUES
                error_msg = str(e)
                if 'username' in error_msg.lower():
                    messages.error(request, "❌ Ce nom d'utilisateur est déjà utilisé.")
                elif 'email' in error_msg.lower():
                    messages.error(request, "❌ Cette adresse email est déjà utilisée.")
                elif 'unique' in error_msg.lower():
                    messages.error(request, "❌ Violation de contrainte d'unicité.")
                else:
                    messages.error(request, f"❌ Erreur d'intégrité : {error_msg}")
                
                # 🗑️ NETTOYAGE SI UTILISATEUR CRÉÉ
                if 'user' in locals() and hasattr(user, 'pk') and user.pk:
                    user.delete(force_policy=True)
                    
            except Exception as e:
                # 🔄 RÉACTIVER LE SIGNAL EN CAS D'ERREUR GÉNÉRIQUE
                signals.post_save.connect(create_user_profile, sender=User)
                
                # 🚨 GESTION DES ERREURS GÉNÉRIQUES
                error_type = type(e).__name__
                messages.error(
                    request, 
                    f"❌ Erreur [{error_type}] : {str(e)[:100]}..."
                )
                
                # 🗑️ NETTOYAGE SI UTILISATEUR CRÉÉ
                if 'user' in locals() and hasattr(user, 'pk') and user.pk:
                    try:
                        user.delete(force_policy=True)
                    except:
                        pass
                        
                # 📋 LOG ERREUR
                print(f"❌ ERREUR CRÉATION PROFESSEUR: {error_type} - {e}")
                
        else:
            # 📝 VALIDATION DES FORMULAIRES ÉCHOUÉE
            error_count = len(user_form.errors) + len(prof_form.errors)
            messages.error(
                request, 
                f"❌ Validation échouée ({error_count} erreur{'s' if error_count > 1 else ''}). "
                "Veuillez corriger les champs marqués en rouge."
            )
            
            # 🎯 AJOUT DES CLASSES D'ERREUR AUX CHAMPS
            for field in user_form:
                if field.errors:
                    field.field.widget.attrs['class'] = field.field.widget.attrs.get('class', '') + ' is-invalid'
            
            for field in prof_form:
                if field.errors:
                    field.field.widget.attrs['class'] = field.field.widget.attrs.get('class', '') + ' is-invalid'

    # 🎨 RENDU DU TEMPLATE
    context = {
        'user_form': user_form,
        'prof_form': prof_form,
        'page_title': 'Créer un Professeur',
        'breadcrumbs': [
            {'name': 'Dashboard', 'url': 'accounts:dashboard'},
            {'name': 'Professeurs', 'url': 'accounts:liste_professeurs'},
            {'name': 'Créer', 'url': 'accounts:creer_professeur'},
        ]
    }
    
    return render(request, 'accounts/creer_professeur.html', context)


# @login_required
# @user_passes_test(can_manage_users)
# def creer_professeur(request):
#     user_form = UserForm(request.POST or None)
#     prof_form = ProfesseurForm(request.POST or None)

#     if request.method == 'POST':
#         if user_form.is_valid() and prof_form.is_valid():
#             try:
#                 # ✅ DÉSACTIVER le signal temporairement
#                 from django.db.models import signals
#                 from .signals import create_user_profile
#                 signals.post_save.disconnect(create_user_profile, sender=User)
                
#                 user = user_form.save(commit=False)
#                 user.role = User.Role.PROFESSEUR
#                 user.first_login = True

#                 password = user_form.cleaned_data.get('password')
#                 if password:
#                     user.set_password(password)
#                 else:
#                     messages.error(request, "Le mot de passe est obligatoire.")
#                     # ✅ RÉACTIVER le signal avant de retourner
#                     signals.post_save.connect(create_user_profile, sender=User)
#                     return render(request, 'accounts/creer_professeur.html', {
#                         'user_form': user_form,
#                         'prof_form': prof_form,
#                     })

#                 user.save()

#                 # ✅ Maintenant créer le profil Professeur manuellement
#                 # (le signal ne s'est pas déclenché)
#                 professeur = prof_form.save(commit=False)
#                 professeur.user = user
#                 professeur.save()
                
#                 messages.success(request, "Professeur créé avec succès")
                
#                 # ✅ RÉACTIVER le signal
#                 signals.post_save.connect(create_user_profile, sender=User)
#                 return redirect('accounts:liste_professeurs')

#             except IntegrityError as e:
#                 # ✅ RÉACTIVER le signal en cas d'erreur
#                 signals.post_save.connect(create_user_profile, sender=User)
#                 messages.error(request, f"Erreur lors de la création : {e}")
#                 if 'user' in locals() and user.pk:
#                     user.delete()
#             except Exception as e:
#                 # ✅ RÉACTIVER le signal en cas d'erreur
#                 signals.post_save.connect(create_user_profile, sender=User)
#                 messages.error(request, f"Erreur inattendue : {e}")
#                 if 'user' in locals() and user.pk:
#                     user.delete()
#         else:
#             messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
#     else:
#         user_form = UserForm()
#         prof_form = ProfesseurForm()

#     return render(request, 'accounts/creer_professeur.html', {
#         'user_form': user_form,
#         'prof_form': prof_form,
#     })


@login_required
def dashboard(request):
    user = request.user
    
    if user.role == User.Role.ADMIN:
        from academics.models import Faculte, Cours
        from grades.models import Note
        
        # Statistiques de base
        stats = {
            'etudiants': Etudiant.objects.count(),
            'professeurs': Professeur.objects.count(),
            'facultes': Faculte.objects.count(),
            'cours': Cours.objects.count(),
            'admins': Admin.objects.count(),
        }
        
        # Données supplémentaires pour le dashboard
        notes_soumises = Note.objects.filter(statut='soumise')
        # Calculer les étudiants sans cours (exemple)
        from django.db.models import Count
        etudiants_sans_cours = Etudiant.objects.annotate(
            nb_cours=Count('inscriptions')
        ).filter(nb_cours=0)
        
        context = {
            'role': 'admin',
            'stats': stats,
            'notes_soumises': notes_soumises,
            'etudiants_sans_cours': etudiants_sans_cours,
        }
    
    elif user.role == User.Role.PROFESSEUR:
        from academics.models import Cours
        from django.db.models import Count, Exists, OuterRef, Subquery
        from grades.models import InscriptionCours
        
        # OPTION A: Annotation avec COUNT des inscriptions
        cours_assignes = Cours.objects.filter(
            professeur=user
        ).annotate(
            nb_etudiants_inscrits=Count('inscriptions', distinct=True)
        ).select_related('faculte')
        
        # OPTION B: Annotation avec SUBQUERY (plus performant pour les grandes BDD)
        cours_assignes = Cours.objects.filter(
            professeur=user
        ).annotate(
            nb_inscrits=Subquery(
                InscriptionCours.objects.filter(
                    cours=OuterRef('pk')
                ).values('cours')
                .annotate(count=Count('*'))
                .values('count')[:1]
            )
        ).select_related('faculte')
        
        # Pour chaque cours, afficher aussi le nombre d'étudiants concernés
        for cours in cours_assignes:
            cours.nb_concernes = cours.etudiants_concernes().count()
            cours.nb_inscrits_reel = cours.inscriptions.count()
        
        context = {
            'role': 'professeur',
            'cours_assignes': cours_assignes
        }
    
    elif user.role == User.Role.ETUDIANT:
        from grades.models import Note, InscriptionCours
        from academics.models import Cours

        if hasattr(user, 'etudiant'):
            notes_recentes = Note.objects.filter(
                etudiant=user.etudiant,
                statut='publiée'
            )[:5]

            cours_inscrits = Cours.objects.filter(
                inscriptions__etudiant=user.etudiant
            ).distinct()

            context = {
                'role': 'etudiant',
                'etudiant': user.etudiant,
                'notes_recentes': notes_recentes,
                'cours_inscrits': cours_inscrits
            }
        else:
            context = {'role': 'etudiant', 'etudiant': None}
    
    else:
        context = {'role': 'unknown'}
    
    return render(request, 'accounts/dashboard.html', context)

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q

# ✅ CORRECTION : UTILISER LES PERMISSIONS GRANULAIRES
@login_required
@user_passes_test(can_manage_users)  # ✅ Au lieu de is_admin
def liste_etudiants(request):
    search = request.GET.get('search', '')
    etudiants_list = Etudiant.objects.select_related('user', 'faculte').order_by('faculte', 'niveau', 'user__last_name')
    if search:
        etudiants_list = etudiants_list.filter(
            user__last_name__icontains=search
        ) | etudiants_list.filter(matricule__icontains=search)
        if not etudiants_list.exists():
            messages.info(request, "Aucun étudiant ne correspond à votre recherche.")

    paginator = Paginator(etudiants_list, 10)
    page_number = request.GET.get('page')
    etudiants = paginator.get_page(page_number)
    return render(request, 'accounts/liste_etudiants.html', {'etudiants': etudiants})


@login_required
@user_passes_test(can_manage_users)
def rechercher_etudiants_ajax(request):
    search = request.GET.get('q', '')

    etudiants = Etudiant.objects.select_related('user', 'faculte').filter(
        Q(user__last_name__icontains=search) |
        Q(user__first_name__icontains=search) |
        Q(matricule__icontains=search) |
        Q(faculte__nom__icontains=search)
    ).order_by('user__last_name')[:20]

    data = []
    for e in etudiants:
        data.append({
            'id': e.id,
            'matricule': e.matricule,
            'nom': e.user.get_full_name(),
            'faculte': e.faculte.nom,
            'niveau': e.get_niveau_display(),
            'telephone': e.user.telephone or '—',
            'date': e.date_inscription.strftime('%d/%m/%Y')
        })

    return JsonResponse({'etudiants': data})



# ✅ CORRECTION : UTILISER LES PERMISSIONS GRANULAIRES  
@login_required
@user_passes_test(can_manage_users)  # ✅ Au lieu de is_admin
def liste_professeurs(request):
    search = request.GET.get('search', '')
    prof_list = Professeur.objects.select_related('user').order_by('user__last_name')
    if search:
        prof_list = prof_list.filter(user__last_name__icontains=search) | prof_list.filter(specialite__icontains=search)
        if not prof_list.exists():
            messages.info(request, "Aucun professeur ne correspond à votre recherche.")

    paginator = Paginator(prof_list, 10)
    page_number = request.GET.get('page')
    professeurs = paginator.get_page(page_number)
    return render(request, 'accounts/liste_professeurs.html', {'professeurs': professeurs})


from django.http import JsonResponse
from django.db.models import Q

@login_required
@user_passes_test(can_manage_users)
def rechercher_professeurs_ajax(request):
    search = request.GET.get('q', '')

    profs = Professeur.objects.select_related('user').filter(
        Q(user__last_name__icontains=search) |
        Q(user__first_name__icontains=search) |
        Q(specialite__icontains=search) |
        Q(statut__icontains=search)
    ).order_by('user__last_name')[:20]

    data = []
    for p in profs:
        data.append({
            'id': p.id,
            'nom': p.user.get_full_name(),
            'specialite': p.specialite,
            'statut': p.statut,
            'date': p.date_embauche.strftime('%d/%m/%Y'),
            'telephone': p.user.telephone or '—'
        })

    return JsonResponse({'professeurs': data})



# === VUES DE MODIFICATION ===

@login_required
@user_passes_test(can_manage_users)
def modifier_etudiant(request, etudiant_id):
    """Modifier un étudiant existant"""
    etudiant = get_object_or_404(Etudiant, id=etudiant_id)
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, instance=etudiant.user)  # ← Utiliser UserEditForm
        etu_form = EtudiantForm(request.POST, instance=etudiant)
        
        if user_form.is_valid() and etu_form.is_valid():
            user_form.save()
            etu_form.save()
            messages.success(request, "Étudiant modifié avec succès")
            return redirect('accounts:liste_etudiants')
    else:
        user_form = UserEditForm(instance=etudiant.user)  # ← Utiliser UserEditForm
        etu_form = EtudiantForm(instance=etudiant)
    
    return render(request, 'accounts/modifier_etudiant.html', {
        'user_form': user_form,
        'etu_form': etu_form,
        'etudiant': etudiant
    })


@login_required
@user_passes_test(can_manage_users)
def modifier_professeur(request, professeur_id):
    """Modifier un professeur existant"""
    professeur = get_object_or_404(Professeur, id=professeur_id)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=professeur.user)
        prof_form = ProfesseurForm(request.POST, instance=professeur)
        
        if user_form.is_valid() and prof_form.is_valid():
            user_form.save()
            prof_form.save()
            messages.success(request, "Professeur modifié avec succès")
            return redirect('accounts:liste_professeurs')
    else:
        user_form = UserForm(instance=professeur.user)
        prof_form = ProfesseurForm(instance=professeur)
    
    return render(request, 'accounts/modifier_professeur.html', {
        'user_form': user_form,
        'prof_form': prof_form,
        'professeur': professeur
    })

@login_required
@user_passes_test(can_manage_users)
def supprimer_etudiant(request, etudiant_id):
    """Supprimer un étudiant"""
    etudiant = get_object_or_404(Etudiant, id=etudiant_id)
    
    if request.method == 'POST':
        user = etudiant.user
        etudiant.delete()
        user.delete()
        messages.success(request, "Étudiant supprimé avec succès")
        return redirect('accounts:liste_etudiants')
    
    return render(request, 'accounts/supprimer_etudiant.html', {
        'etudiant': etudiant
    })

@login_required
@user_passes_test(can_manage_users)
def supprimer_professeur(request, professeur_id):
    """Supprimer un professeur"""
    professeur = get_object_or_404(Professeur, id=professeur_id)
    
    if request.method == 'POST':
        user = professeur.user
        professeur.delete()
        user.delete()
        messages.success(request, "Professeur supprimé avec succès")
        return redirect('accounts:liste_professeurs')
    
    return render(request, 'accounts/supprimer_professeur.html', {
        'professeur': professeur
    })




# Fonction de test pour l'accès
def can_manage_users(user):
    return user.is_staff or user.role in ['admin', 'manager']  # à adapter selon tes rôles

@login_required
@user_passes_test(can_manage_users)
def export_professeurs_csv(request):
    search = request.GET.get('q', '').strip()

    profs = Professeur.objects.select_related('user')

    if search:
        profs = profs.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(specialite__icontains=search)
        )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="professeurs.csv"'

    output = io.TextIOWrapper(response, encoding='utf-8-sig', newline='')
    writer = csv.writer(output)

    # Entête
    writer.writerow(['NOM', 'PRENOM', 'SPECIALITE', 'STATUT', 'TELEPHONE'])

    # Données
    for p in profs:
        writer.writerow([
            p.user.last_name,
            p.user.first_name,
            p.specialite,
            p.statut,
            p.user.telephone or ''
        ])

    output.flush()
    return response


@login_required
@user_passes_test(can_manage_users)
def export_etudiants_csv(request):
    search = request.GET.get('q', '').strip()

    etudiants = Etudiant.objects.select_related('user', 'faculte')

    if search:
        etudiants = etudiants.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(matricule__icontains=search)
        )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="etudiants.csv"'

    output = io.TextIOWrapper(response, encoding='utf-8-sig', newline='')
    writer = csv.writer(output)

    # Entête
    writer.writerow(['MATRICULE', 'NOM', 'PRENOM', 'FACULTE', 'NIVEAU'])

    # Données
    for e in etudiants:
        writer.writerow([
            e.matricule,
            e.user.last_name,
            e.user.first_name,
            e.faculte.nom,
            e.get_niveau_display()
        ])

    output.flush()
    return response



#vues pour gerer utilisateur
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .models import User, Etudiant, Professeur

# Décorateur pour vérifier si l'utilisateur est admin
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != User.Role.ADMIN:
            messages.error(request, "❌ Accès réservé aux administrateurs")
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@admin_required
def gestion_utilisateurs(request):
    """
    Admin: Liste et gestion de tous les utilisateurs
    """
    # Paramètres de filtrage
    role = request.GET.get('role', '')
    statut = request.GET.get('statut', '')
    search = request.GET.get('search', '')
    
    # Base queryset
    utilisateurs = User.objects.all()
    
    # Appliquer les filtres
    if role:
        utilisateurs = utilisateurs.filter(role=role)
    
    if statut == 'actif':
        utilisateurs = utilisateurs.filter(is_active=True)
    elif statut == 'inactif':
        utilisateurs = utilisateurs.filter(is_active=False)
    
    if search:
        utilisateurs = utilisateurs.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Trier par date d'inscription (plus récent d'abord)
    utilisateurs = utilisateurs.order_by('-date_joined')
    
    context = {
        'utilisateurs': utilisateurs,
        'roles': User.Role.choices,
        'selected_role': role,
        'selected_statut': statut,
        'search_query': search,
    }
    
    return render(request, 'accounts/gestion_utilisateurs.html', context)

@login_required
@admin_required
def detail_utilisateur(request, user_id):
    """
    Admin: Détail d'un utilisateur avec actions
    """
    utilisateur = get_object_or_404(User, id=user_id)
    
    # Récupérer les informations spécifiques selon le rôle
    infos_supplementaires = None
    if utilisateur.role == User.Role.ETUDIANT:
        try:
            infos_supplementaires = Etudiant.objects.get(user=utilisateur)
        except Etudiant.DoesNotExist:
            pass
    elif utilisateur.role == User.Role.PROFESSEUR:
        try:
            infos_supplementaires = Professeur.objects.get(user=utilisateur)
        except Professeur.DoesNotExist:
            pass
    
    context = {
        'utilisateur': utilisateur,
        'infos_supplementaires': infos_supplementaires,
    }
    
    return render(request, 'accounts/detail_utilisateur.html', context)

@login_required
@admin_required
def toggle_activation(request, user_id):
    """
    Admin: Activer/désactiver un compte utilisateur
    """
    utilisateur = get_object_or_404(User, id=user_id)
    
    # Empêcher de désactiver son propre compte
    if utilisateur == request.user:
        messages.error(request, "❌ Vous ne pouvez pas désactiver votre propre compte")
        return redirect('accounts:detail_utilisateur', user_id=user_id)
    
    # Toggle l'état actif/inactif
    utilisateur.is_active = not utilisateur.is_active
    utilisateur.save()
    
    if utilisateur.is_active:
        messages.success(request, f"✅ Compte de {utilisateur.get_full_name()} activé avec succès")
    else:
        messages.warning(request, f"⚠️ Compte de {utilisateur.get_full_name()} désactivé avec succès")
    
    return redirect('accounts:detail_utilisateur', user_id=user_id)

@login_required
@admin_required
def changer_role(request, user_id):
    """
    Admin: Changer le rôle d'un utilisateur
    """
    utilisateur = get_object_or_404(User, id=user_id)
    
    # Empêcher de modifier son propre rôle
    if utilisateur == request.user:
        messages.error(request, "❌ Vous ne pouvez pas modifier votre propre rôle")
        return redirect('accounts:detail_utilisateur', user_id=user_id)
    
    if request.method == 'POST':
        nouveau_role = request.POST.get('role')
        
        if nouveau_role in [role[0] for role in User.Role.choices]:
            ancien_role = utilisateur.get_role_display()
            utilisateur.role = nouveau_role
            utilisateur.save()
            
            messages.success(request, 
                f"✅ Rôle de {utilisateur.get_full_name()} changé: {ancien_role} → {utilisateur.get_role_display()}"
            )
    
    return redirect('accounts:detail_utilisateur', user_id=user_id)


@login_required
def mon_profil(request):
    """Affiche et permet de modifier les informations personnelles de l'utilisateur"""
    user = request.user
    
    # Récupérer les informations supplémentaires selon le rôle
    info_supplementaires = {}
    
    if user.role == 'student':
        try:
            etudiant = Etudiant.objects.get(user=user)
            info_supplementaires = {
                'matricule': etudiant.matricule,
                'faculte': etudiant.faculte,
                'niveau': etudiant.get_niveau_display(),
                'date_inscription': etudiant.date_inscription,
                'adresse': etudiant.adresse,
                'date_naissance': etudiant.date_naissance,
                'sexe': etudiant.get_sexe_display(),
                'telephone_parent': etudiant.telephone_parent,
            }
        except ObjectDoesNotExist:
            pass
    
    elif user.role == 'prof':
        try:
            professeur = Professeur.objects.get(user=user)
            info_supplementaires = {
                'specialite': professeur.specialite,
                'date_embauche': professeur.date_embauche,
                'statut': professeur.get_statut_display(),
            }
        except ObjectDoesNotExist:
            pass
    
    elif user.role == 'admin':
        try:
            admin = Admin.objects.get(user=user)
            info_supplementaires = {
                'date_nomination': admin.date_nomination,
                'niveau_acces': admin.get_niveau_acces_display(),
            }
        except ObjectDoesNotExist:
            pass
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vos informations ont été mises à jour avec succès.')
            return redirect('accounts:mon_profil')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = UserProfileForm(instance=user)
    
    context = {
        'user': user,
        'form': form,
        'info_supp': info_supplementaires,
    }
    
    return render(request, 'accounts/mon_profil.html', context)
