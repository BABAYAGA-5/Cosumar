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
    deleted_by = models.ForeignKey('auth_service.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True)

class Sujet(models.Model):
    id = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=100)
    description = models.TextField()
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey('auth_service.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True)

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
        ('stage', 'Stage'),
        ('pfe', 'PFE'),
        ('alternance', 'Alternance'),
    ], default='stage')
    sujet = models.ForeignKey(Sujet, on_delete=models.CASCADE, related_name='stages', null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    prolongation = models.BooleanField(default=False)
    statut = models.CharField(
        max_length=50,
        choices=[
            ('annule', 'Annulé'),
            ('en_attente_depot_dossier', 'En attente de dépôt de dossier'),
            ('expire', 'Expiré'),
            ('en_attente_visite_medicale', 'En attente de visite médicale'),
            ('en_attente_signature_de_l_encadrant', 'En attente de signature de l\'encadrant'),
            ('en_attente_signature_du_responsable_RH', 'En attente de signature du responsable RH'),
            ('en_attente_signature_du_stagiaire', 'En attente de signature du stagiaire'),
            ('stage_en_cours', 'Stage en cours'),
            ('en_attente_depot_rapport', 'En attente de dépôt de rapport'),
            ('termine', 'Terminé')
        ],
        default='en_attente_depot_dossier'
    )
    convention = models.BinaryField(null=True, blank=True)
    assurance = models.BinaryField(null=True, blank=True)
    lettre_motivation = models.BinaryField(null=True, blank=True)
    cv = models.BinaryField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey('auth_service.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True)

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


class Meta:
    verbose_name = "Candidature"