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
    is_active = models.BooleanField(default=True)
    role = models.CharField(max_length=50, choices=[
    ('admin', 'Administrateur'),
    ('admin_rh', 'Admin RH'),
    ('utilisateur_rh', 'Utilisateur RH'),
    ('utilisateur', 'Utilisateur'),
    ], default='utilisateur_rh')

    departement = models.CharField(max_length=100, choices=[
        ('digital_factory', 'Digital Factory'),
        ('ressources_humaines', 'Ressources Humaines'),
        ('finance', 'Finance'),
        ('marketing', 'Marketing'),
        ('maintenance', 'Maintenance')
    ], blank=True, null=True)

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'
    is_anonymous = False
    is_authenticated = True
    

    def __str__(self):
        return f"{self.prenom} {self.nom}"
    


