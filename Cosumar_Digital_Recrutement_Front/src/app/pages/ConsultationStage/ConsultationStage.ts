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
        const stagiaireData = response.stages?.map((stage: any) => ({
          matricule: stage.stagiaire?.matricule || stage.stagiaire_id,
          nom: stage.stagiaire?.nom || '',
          prenom: stage.stagiaire?.prenom || '',
          statut: stage.statut,
          sujet: stage.sujet?.titre || 'Non défini',
          nature: stage.nature,
          date_debut: stage.date_debut,
          date_fin: stage.date_fin
        })) || [];

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
    // Navigate to stagiaire details page
    this.router.navigate(['/dashboardpage/stages', stagiaire.matricule]);
  }

  getStatusText(statut: string): string {
    const statusTexts: { [key: string]: string } = {
      'annule': 'Annulé',
      'en_attente_depot_dossier': 'En attente de dépôt',
      'expire': 'Expiré',
      'en_attente_visite_medicale': 'Visite médicale',
      'en_attente_signature_de_l_encadrant': 'Signature encadrant',
      'en_attente_signature_du_responsable_RH': 'Signature RH',
      'en_attente_signature_du_stagiaire': 'Signature stagiaire',
      'stage_en_cours': 'En cours',
      'en_attente_depot_rapport': 'Dépôt rapport',
      'termine': 'Terminé'
    };
    return statusTexts[statut] || statut;
  }

  getNatureText(nature: string): string {
    const natureTexts: { [key: string]: string } = {
      'stage': 'Stage',
      'pfe': 'PFE',
      'alternance': 'Alternance'
    };
    return natureTexts[nature] || nature;
  }
}
