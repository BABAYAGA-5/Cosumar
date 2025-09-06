import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Router } from '@angular/router';

interface UserProfile {
  id: number;
  nom: string;
  prenom: string;
  email: string;
  departement: string;
  role: string;
  is_active: boolean;
  date_joined: string;
}

@Component({
  selector: 'app-profile-page',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ProfilePage.html',
  styleUrl: './ProfilePage.css'
})
export class ProfilePage implements OnInit {
  private http = inject(HttpClient);
  private router = inject(Router);

  // User profile data
  userProfile = signal<UserProfile | null>(null);
  isLoading = signal(true);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.loadUserProfile();
  }

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access');
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }

  loadUserProfile(): void {
    this.isLoading.set(true);
    this.error.set(null);

    // Get current user ID from localStorage or JWT token
    const userId = localStorage.getItem('user_id');
    
    if (!userId) {
      this.error.set('Utilisateur non trouvé');
      this.isLoading.set(false);
      return;
    }

    this.http.get<UserProfile>(`${environment.apiUrl}auth/users/${userId}/`, {
      headers: this.getAuthHeaders()
    }).subscribe({
      next: (profile) => {
        this.userProfile.set(profile);
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Error loading user profile:', error);
        this.error.set('Erreur lors du chargement du profil');
        this.isLoading.set(false);
      }
    });
  }

  goBack(): void {
    this.router.navigate(['/dashboard']);
  }

  editProfile(): void {
    // Navigate to edit profile page (to be implemented)
    console.log('Edit profile functionality to be implemented');
  }

  // Helper methods for template
  formatDate(dateString: string | undefined): string {
    if (!dateString) return 'Non spécifié';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  getDepartmentDisplayName(departementCode: string): string {
    const departments: { [key: string]: string } = {
      'finance': 'Finance',
      'digital_factory': 'Digital Factory',
      'maintenance': 'Maintenance',
      'production': 'Production',
      'qualite': 'Qualité',
      'rh': 'Ressources Humaines',
      'commercial': 'Commercial',
      'logistique': 'Logistique'
    };
    return departments[departementCode] || departementCode;
  }

  getRoleDisplayName(role: string): string {
    const roles: { [key: string]: string } = {
      'admin': 'Administrateur',
      'rh': 'Ressources Humaines',
      'chef_departement': 'Chef de Département',
      'encadrant': 'Encadrant'
    };
    return roles[role] || role;
  }
}
