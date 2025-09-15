import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { StagiaireCardComponent, StagiaireData } from '../../components/StagiaireCard/StagiaireCard';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'ConsultationStage',
  standalone: true,
  imports: [CommonModule, FormsModule, StagiaireCardComponent],
  templateUrl: './ConsultationStage.html',
  styleUrl: './ConsultationStage.css'
})
export class ConsultationStage implements OnInit {
  private http = inject(HttpClient);
  private router = inject(Router);
  
  // Data signals
  stagiaires = signal<StagiaireData[]>([]);
  filteredStagiaires = signal<StagiaireData[]>([]);
  isLoading = signal(true);
  errorMessage = signal<string | null>(null);

  // Filter properties
  selectedStatus = '';
  selectedNature = '';
  searchQuery = '';
  viewMode: 'grid' | 'list' = 'grid';

  ngOnInit(): void {
    this.loadStagiaires();
  }

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access');
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }

  loadStagiaires(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.http.get<any>(`${environment.apiUrl}resume/chercher_stages/`, {
      headers: this.getAuthHeaders()
    }).subscribe({
      next: (response) => {
        // Transform Django model data to match StagiaireData interface
        // Handle both array response and object with stages property
        const stages = Array.isArray(response) ? response : (response.stages || []);
        
        const stagiaireData = stages.map((stage: any) => ({
          stageId: stage.id,  // Add stage ID for navigation
          matricule: stage.stagiaire?.matricule || stage.stagiaire_id || stage.id?.toString() || '',
          nom: stage.stagiaire?.nom || stage.stagiaire__nom || '',
          prenom: stage.stagiaire?.prenom || stage.stagiaire__prenom || '',
          statut: stage.statut,
          sujet: stage.sujet?.titre || stage.sujet__titre || 'Non défini',
          nature: stage.nature,
          date_debut: stage.date_debut,
          date_fin: stage.date_fin,
          introduit_par: stage.introduit_par ? {
            id: stage.introduit_par.id,
            nom: stage.introduit_par.nom,
            prenom: stage.introduit_par.prenom,
            email: stage.introduit_par.email,
            departement: stage.introduit_par.departement
          } : undefined
        }));

        console.log('Transformed stagiaire data:', stagiaireData);
        this.stagiaires.set(stagiaireData);
        this.filteredStagiaires.set(stagiaireData);
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Error loading stagiaires:', error);
        this.errorMessage.set('Erreur lors du chargement des stages');
        this.isLoading.set(false);
      }
    });
  }

  filterByStatus(): void {
    this.applyFilters();
  }

  filterByNature(): void {
    this.applyFilters();
  }

  onSearchChange(): void {
    this.applyFilters();
  }

  private applyFilters(): void {
    let filtered = this.stagiaires();

    // Filter by status
    if (this.selectedStatus) {
      filtered = filtered.filter(s => s.statut === this.selectedStatus);
    }

    // Filter by nature
    if (this.selectedNature) {
      filtered = filtered.filter(s => s.nature === this.selectedNature);
    }

    // Filter by search query
    if (this.searchQuery.trim()) {
      const query = this.searchQuery.toLowerCase().trim();
      filtered = filtered.filter(s => 
        s.nom.toLowerCase().includes(query) ||
        s.prenom.toLowerCase().includes(query) ||
        s.matricule.toLowerCase().includes(query) ||
        `${s.prenom} ${s.nom}`.toLowerCase().includes(query)
      );
    }

    this.filteredStagiaires.set(filtered);
  }

  clearFilters(): void {
    this.selectedStatus = '';
    this.selectedNature = '';
    this.searchQuery = '';
    this.filteredStagiaires.set(this.stagiaires());
  }

  setViewMode(mode: 'grid' | 'list'): void {
    this.viewMode = mode;
  }

  onStagiaireClick(stagiaire: StagiaireData): void {
    // Navigate to stage details page using stage ID
    console.log('Navigating to stage details for stage ID:', stagiaire.stageId);
    console.log('Stage data:', stagiaire);
    this.router.navigate(['/dashboardpage/stage', stagiaire.stageId]);
  }

  getStatusText(statut: string): string {
    const statusTexts: { [key: string]: string } = {
      'annule': 'Annulé',
      'en_attente_depot_dossier': 'En attente de dépôt de dossier',
      'expire': 'Expiré',
      'en_attente_visite_medicale': 'En attente de visite médicale',
      'en_attente_des_signatures': 'En attente de signatures',
      'stage_en_cours': 'Stage en cours',
      'en_attente_depot_rapport': 'En attente de dépôt de rapport',
      'en_attente_signature_du_rapport_par_l_encadrant': 'En attente de signature du rapport par l\'encadrant',
      'termine': 'Terminé'
    };
    return statusTexts[statut] || statut;
  }

  getNatureText(nature: string): string {
    const natureTexts: { [key: string]: string } = {
      'stage_observation': 'Stage d\'observation',
      'pfe': 'PFE',
      'stage_application': 'Stage d\'application'
    };
    return natureTexts[nature] || nature;
  }
}
