from django.db import models
from datetime import timedelta
from datetime import datetime

from numpy import extract

class Stagiaire(models.Model):
    matricule = models.CharField(primary_key=True, max_length=8, default='')
    prenom = models.CharField(max_length=100, null=True, blank=True)
    nom = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    num_tel = models.CharField(max_length=15, unique=True, blank=True, null=True)
    date_naissance = models.DateField(null=True, blank=True)
    cin = models.BinaryField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey('auth_service.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, related_name="stagiaires_deleted")

class Sujet(models.Model):
    id = models.AutoField(primary_key=True)
    created_by = models.ForeignKey(
        'auth_service.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sujets_created" 
    )
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    titre = models.CharField(max_length=100)
    description = models.TextField()
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'auth_service.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sujets_deleted"
    )


    def __str__(self):
        return self.titre

class Stage(models.Model):
    id = models.AutoField(primary_key=True)
    stagiaire = models.ForeignKey(
        Stagiaire, 
        on_delete=models.CASCADE, 
        related_name='stages', 
        to_field='matricule',
        db_column='stagiaire_id'
    )
    nature = models.CharField(max_length=50, choices=[
        ('stage_observation', 'Stage d\'observation'),
        ('stage_application', 'Stage d\'application'),
        ('pfe', 'PFE'),
    ], default='stage_observation')
    introduit_par = models.ForeignKey('auth_service.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True, default=None, related_name="stagiaires_introduits")
    sujet = models.ForeignKey(Sujet, on_delete=models.CASCADE, related_name='stages', null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    prolongation = models.DateField(null=True, blank=True, default=None)
    statut = models.CharField(
        max_length=50,
        choices=[
            ('annule', 'Annulé'),
            ('en_attente_depot_dossier', 'En attente de dépôt de dossier'),
            ('expire', 'Expiré'),
            ('en_attente_visite_medicale', 'En attente de visite médicale'),
            ('en_attente_des_signatures', 'En attente de signatures'),
            ('stage_en_cours', 'Stage en cours'),
            ('en_attente_depot_rapport', 'En attente de dépôt de rapport'),
            ('en_attente_signature_du_rapport_par_l_encadrant', 'En attente de signature du rapport par l\'encadrant'),
            ('termine', 'Terminé')
        ],
        default='en_attente_depot_dossier'
    )
    # New JSON field to store all signature data and demande de stage information
    demande_de_stage_data = models.JSONField(null=True, blank=True, default=dict)
    convention = models.BinaryField(null=True, blank=True)
    assurance = models.BinaryField(null=True, blank=True)
    lettre_motivation = models.BinaryField(null=True, blank=True)
    cv = models.BinaryField(null=True, blank=True)
    demande_de_stage = models.BinaryField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey('auth_service.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True)

    def initialize_demande_data(self):
        """Initialize the demande_de_stage_data JSON structure"""
        if not self.demande_de_stage_data:
            self.demande_de_stage_data = {
                'signatures': {
                    'encadrant': None,
                    'responsable_de_service': None,
                    'responsable_rh': None
                },
                'document_data': {
                    'nom': '',
                    'prenom': '',
                    'cin': '',
                    'telephone': '',
                    'specialite': '',
                    'etablissement': '',
                    'periode_du': '',
                    'periode_au': '',
                    'encadrant': '',
                    'service': '',
                    'periode_accordee_du': '',
                    'periode_accordee_au': '',
                    'sujet': '',
                    'created_at': None,
                    'last_modified': None
                },
                'signature_status': {
                    'all_signed': False,
                    'signatures_count': 0
                }
            }

    def add_signature(self, role, user, signature_date=None):
        """Add a signature for a specific role"""
        from datetime import datetime
        if not signature_date:
            signature_date = datetime.now().strftime('%d/%m/%Y')
        
        self.initialize_demande_data()
        
        signature_info = {
            'user_id': user.id,
            'email': user.email,
            'full_name': f"{user.prenom} {user.nom}".title() if user.prenom and user.nom else user.email,
            'signed_at': signature_date,
            'role': role
        }
        
        self.demande_de_stage_data['signatures'][role] = signature_info
        self.demande_de_stage_data['document_data']['last_modified'] = signature_date
        
        # Update signature count and status
        signed_count = sum(1 for sig in self.demande_de_stage_data['signatures'].values() if sig is not None)
        self.demande_de_stage_data['signature_status']['signatures_count'] = signed_count
        self.demande_de_stage_data['signature_status']['all_signed'] = signed_count == 3

    def update_document_data(self):
        """Update the document data in the JSON structure with current stage and stagiaire info"""
        self.initialize_demande_data()
        
        self.demande_de_stage_data['document_data'].update({
            'nom': self.stagiaire.nom.upper() if self.stagiaire.nom else '',
            'prenom': self.stagiaire.prenom.title() if self.stagiaire.prenom else '',
            'cin': self.stagiaire.matricule if self.stagiaire.matricule else '',
            'telephone': self.stagiaire.num_tel if self.stagiaire.num_tel else '',
            'periode_du': self.date_debut.strftime('%d/%m/%Y') if self.date_debut else '',
            'periode_au': self.date_fin.strftime('%d/%m/%Y') if self.date_fin else '',
            'periode_accordee_du': self.date_debut.strftime('%d/%m/%Y') if self.date_debut else '',
            'periode_accordee_au': self.date_fin.strftime('%d/%m/%Y') if self.date_fin else '',
            'sujet': self.sujet.titre if self.sujet and self.sujet.titre else '',
            'encadrant': self.sujet.created_by.prenom + ' ' + self.sujet.created_by.nom if self.sujet and self.sujet.created_by and self.sujet.created_by.prenom and self.sujet.created_by.nom else '',
        })

    def get_signature_info(self, role):
        """Get signature information for a specific role"""
        if not self.demande_de_stage_data or 'signatures' not in self.demande_de_stage_data:
            return None
        return self.demande_de_stage_data['signatures'].get(role)

    def is_signed_by_role(self, role):
        """Check if document is signed by a specific role"""
        return self.get_signature_info(role) is not None

    def are_all_signatures_complete(self):
        """Check if all three signatures are present"""
        if not self.demande_de_stage_data:
            return False
        return self.demande_de_stage_data.get('signature_status', {}).get('all_signed', False)

    def get_signatures_status(self):
        """Get a summary of signature status"""
        if not self.demande_de_stage_data:
            return {'encadrant': False, 'responsable_de_service': False, 'responsable_rh': False}
        
        signatures = self.demande_de_stage_data.get('signatures', {})
        return {
            'encadrant': signatures.get('encadrant') is not None,
            'responsable_de_service': signatures.get('responsable_de_service') is not None,
            'responsable_rh': signatures.get('responsable_rh') is not None
        }

    def check_documents_and_expire(self):
        if self.statut == 'accepte':
            if not self.cv or not self.stagiaire.cin or not self.convention or not self.assurance:
                self.statut = 'expire'
                self.save()

    def __str__(self):
        return f"Stage de {self.stagiaire.prenom} {self.stagiaire.nom} ({self.nature})"


class Logs(models.Model):
    id = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey('auth_service.Utilisateur', on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    date_action = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.nom

class Meta:
    demande_de_stage = models.BinaryField(null=True, blank=True)