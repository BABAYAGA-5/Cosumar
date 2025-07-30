from django.db import models

class Candidat(models.Model):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prenom} {self.nom}"
    
class Domaine(models.Model):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100, unique=True)
    keywords = models.JSONField(default=list)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

class Poste(models.Model):
    id = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    date_publication = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=50, choices=[('ouvert', 'Ouvert'), ('ferme', 'Fermé')], default='ouvert')
    domaine = models.OneToOneField(Domaine, blank=True, related_name="job_posts")

    keywords = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.titre
    
class Candidature(models.Model):
    id = models.AutoField(primary_key=True)
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, related_name='candidatures')
    poste = models.ForeignKey(Poste, on_delete=models.CASCADE, related_name='candidatures')
    date_candidature = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=50, choices=[
        ('en_attente', 'En attente'),
        ('accepte', 'Accepté'),
        ('refuse', 'Refusé')
    ], default='en_attente')
    cv = models.BinaryField(blank=False, null=False)

    def __str__(self):
        return f"Candidature de {self.candidat.prenom} {self.candidat.nom} pour le poste de {self.poste}"

