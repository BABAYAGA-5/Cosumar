from django.db import models

class Utilisateur(models.Model):
    id = models.AutoField(primary_key=True)
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mot_de_passe = models.CharField(max_length=256)
    date_creation = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=256, blank=True, null=True)
    validite_token = models.DateTimeField(blank=True, null=True)
    actif = models.BooleanField(default=True)
    role = models.CharField(max_length=50, choices=[
    ('admin', 'Administrateur'),
    ('hr_manager', 'Responsable RH'),
    ('hr_user', 'Utilisateur RH'),
    ], default='hr_user')

    def __str__(self):
        return f"{self.prenom} {self.nom}"
