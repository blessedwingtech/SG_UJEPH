# accounts/middleware.py - CORRECTION COMPLÈTE
from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
import datetime

class AutoLogoutMiddleware:
    """Middleware pour déconnecter automatiquement après période d'inactivité"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout = 300  # 5 minutes en secondes
        self.warning_threshold = 60  # Avertir 60 secondes avant la déconnexion
    
    def __call__(self, request):
        # 🔴 NE PAS mettre à jour last_activity sur les requêtes AJAX d'activité
        is_ajax_activity = (
            request.path == '/comptes/update-activity/' and 
            request.method == 'POST'
        )
        
        if request.user.is_authenticated and not is_ajax_activity:
            current_time = timezone.now()
            
            # Vérifier la dernière activité
            last_activity_str = request.session.get('last_activity')
            
            if last_activity_str:
                try:
                    last_activity = datetime.datetime.fromisoformat(last_activity_str)
                    time_diff = (current_time - last_activity).total_seconds()
                    
                    # Stocker le temps restant dans la session
                    remaining_time = self.timeout - time_diff
                    request.session['auto_logout_remaining'] = max(0, int(remaining_time))
                    
                    print(f"DEBUG: Time diff: {time_diff}s, Remaining: {remaining_time}s")
                    
                    # Si le temps d'inactivité dépasse le timeout
                    if time_diff > self.timeout:
                        # 🔴 NE PAS déconnecter immédiatement - Laisser le JS gérer
                        # Activer l'avertissement avec 0 secondes restantes
                        request.session['auto_logout_warning'] = True
                        request.session['auto_logout_warning_time'] = 0
                        print(f"DEBUG: TIMEOUT REACHED - Déconnexion par JS")
                    
                    # Si on approche de la déconnexion (moins de 60 secondes)
                    # 🔴 SUPPRIMER "and remaining_time > 0"
                    elif remaining_time <= self.warning_threshold:
                        request.session['auto_logout_warning'] = True
                        request.session['auto_logout_warning_time'] = max(0, int(remaining_time))
                        print(f"DEBUG: Warning active - {remaining_time}s remaining")
                    else:
                        if 'auto_logout_warning' in request.session:
                            del request.session['auto_logout_warning']
                            del request.session['auto_logout_warning_time']
                
                except (ValueError, TypeError) as e:
                    print(f"DEBUG: Error parsing timestamp: {e}")
                    pass
            
            # 🔴 Mettre à jour le timestamp UNIQUEMENT si ce n'est pas une requête AJAX d'activité
            request.session['last_activity'] = current_time.isoformat()
            print(f"DEBUG: Updated last_activity to {current_time.isoformat()}")
        
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        """Ajouter le contexte de déconnexion automatique à toutes les réponses"""
        if hasattr(response, 'context_data') and request.user.is_authenticated:
            if response.context_data is None:
                response.context_data = {}
            
            # Ajouter les informations de déconnexion automatique
            response.context_data.update({
                'auto_logout_timeout': self.timeout,
                'auto_logout_remaining': request.session.get('auto_logout_remaining', self.timeout),
                'auto_logout_warning': request.session.get('auto_logout_warning', False),
                'auto_logout_warning_time': request.session.get('auto_logout_warning_time', 0),
                'auto_logout_warning_threshold': self.warning_threshold,
            })
            
            # DEBUG: Afficher les valeurs dans la console Django
            if request.session.get('auto_logout_warning'):
                print(f"DEBUG TEMPLATE: Warning=True, Time={request.session.get('auto_logout_warning_time')}")
        
        return response
    
def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip