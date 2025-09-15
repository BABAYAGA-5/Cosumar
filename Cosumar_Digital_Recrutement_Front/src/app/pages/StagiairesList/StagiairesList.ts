import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-stagiaires-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './StagiairesList.html',
  styleUrls: ['./StagiairesList.css']
})
export class StagiairesList implements OnInit {
  stagiaires: any[] = [];
  loading = true;
  error: string | null = null;
  
  // Filter properties
  searchTerm = '';
  selectedStageStatus = '';
  selectedStageNature = '';
  selectedHasStage = '';
  
  // Pagination properties
  currentPage = 1;
  pageSize = 25;
  totalCount = 0;
  totalPages = 0;
  hasNext = false;
  hasPrevious = false;
  nextPageNumber: number | null = null;
  previousPageNumber: number | null = null;
  
  // Available filter options
  hasStageOptions = [
    { value: '', label: 'Tous les stagiaires' },
    { value: 'true', label: 'Avec stage actuel' },
    { value: 'false', label: 'Sans stage actuel' }
  ];
  
  stageStatusOptions = [
    { value: '', label: 'Tous les statuts' },
    { value: 'en_attente_depot_dossier', label: 'En attente de dépôt de dossier' },
    { value: 'en_attente_visite_medicale', label: 'En attente de visite médicale' },
    { value: 'en_attente_des_signatures', label: 'En attente de signatures' },
    { value: 'stage_en_cours', label: 'Stage en cours' },
    { value: 'en_attente_depot_rapport', label: 'En attente de dépôt de rapport' },
    { value: 'en_attente_signature_du_rapport_par_l_encadrant', label: 'En attente de signature du rapport par l\'encadrant' },
    { value: 'termine', label: 'Terminé' },
    { value: 'annule', label: 'Annulé' },
    { value: 'expire', label: 'Expiré' }
  ];
  
  stageNatureOptions = [
    { value: '', label: 'Tous les types de stage' },
    { value: 'pfe', label: 'Projet de Fin d\'Études (PFE)' },
    { value: 'stage_observation', label: 'Stage d\'Observation' },
    { value: 'stage_application', label: 'Stage d\'Application' }
  ];
  
  private apiUrl = environment.apiUrl + 'resume/stagiaires/';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.loadStagiaires();
  }

  loadStagiaires() {
    const token = localStorage.getItem('access');
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });

    this.loading = true;
    this.error = null;

    // Build URL with filters
    let url = `${this.apiUrl}?page=${this.currentPage}&page_size=${this.pageSize}`;
    
    if (this.searchTerm.trim()) {
      url += `&search=${encodeURIComponent(this.searchTerm.trim())}`;
    }
    if (this.selectedStageStatus) {
      url += `&stage_status=${encodeURIComponent(this.selectedStageStatus)}`;
    }
    if (this.selectedStageNature) {
      url += `&stage_nature=${encodeURIComponent(this.selectedStageNature)}`;
    }
    if (this.selectedHasStage) {
      url += `&has_active_stage=${this.selectedHasStage}`;
    }

    console.log('🔗 API URL with filters:', url); // Debug log
    console.log('📊 Filter parameters:', {
      searchTerm: this.searchTerm,
      selectedStageStatus: this.selectedStageStatus,
      selectedStageNature: this.selectedStageNature,
      selectedHasStage: this.selectedHasStage
    });

    this.http.get<any>(url, { headers }).subscribe({
      next: (response: any) => {
        this.stagiaires = response.results;
        this.totalCount = response.count;
        this.totalPages = response.total_pages;
        this.hasNext = response.has_next;
        this.hasPrevious = response.has_previous;
        this.nextPageNumber = response.next_page_number;
        this.previousPageNumber = response.previous_page_number;
        this.currentPage = response.page;
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Erreur lors du chargement des stagiaires';
        this.loading = false;
        console.error('Erreur:', err);
      }
    });
  }

  nextPage() {
    if (this.hasNext && this.nextPageNumber) {
      this.currentPage = this.nextPageNumber;
      this.loadStagiaires();
    }
  }

  previousPage() {
    if (this.hasPrevious && this.previousPageNumber) {
      this.currentPage = this.previousPageNumber;
      this.loadStagiaires();
    }
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadStagiaires();
    }
  }

  getPageNumbers(): number[] {
    const pages: number[] = [];
    const maxVisible = 5; // Show max 5 page numbers
    
    let startPage = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(this.totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage + 1 < maxVisible) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return pages;
  }

  getCurrentPageMax(): number {
    return Math.min(this.currentPage * this.pageSize, this.totalCount);
  }

  getStatusLabel(status: string): string {
    const statusLabels: { [key: string]: string } = {
      'en_attente_depot_dossier': 'En attente de dépôt de dossier',
      'en_attente_visite_medicale': 'En attente de visite médicale',
      'en_attente_des_signatures': 'En attente de signatures',
      'stage_en_cours': 'Stage en cours',
      'en_attente_depot_rapport': 'En attente de dépôt de rapport',
      'en_attente_signature_du_rapport_par_l_encadrant': 'En attente de signature du rapport par l\'encadrant',
      'termine': 'Terminé',
      'annule': 'Annulé',
      'expire': 'Expiré'
    };
    return statusLabels[status] || status;
  }

  getNatureLabel(nature: string): string {
    const natureLabels: { [key: string]: string } = {
      'pfe': 'Projet de Fin d\'Études',
      'stage_observation': 'Stage d\'Observation',
      'stage_application': 'Stage d\'Application',
    };
    return natureLabels[nature] || nature;
  }

  // Admin permission check
  isAdmin(): boolean {
    // For now, assume user is admin if they have a token
    // This should be properly implemented with JWT token decoding
    return localStorage.getItem('access') !== null;
  }
  
  // Filter methods
  onSearchChange() {
    this.currentPage = 1; // Reset to first page when searching
    this.loadStagiaires();
  }

  onFilterChange() {
    this.currentPage = 1; // Reset to first page when filtering
    this.loadStagiaires();
  }

  onHasStageChange() {
    // Clear stage-specific filters when "Sans stage actuel" is selected
    if (this.selectedHasStage === 'false') {
      this.selectedStageStatus = '';
      this.selectedStageNature = '';
    }
    this.currentPage = 1;
    this.loadStagiaires();
  }

  // Check if stage-specific filters should be enabled
  areStageFiltersEnabled(): boolean {
    return this.selectedHasStage !== 'false';
  }

  clearFilters() {
    this.searchTerm = '';
    this.selectedStageStatus = '';
    this.selectedStageNature = '';
    this.selectedHasStage = '';
    this.currentPage = 1;
    this.loadStagiaires();
  }

  // Delay search to avoid too many API calls
  private searchTimeout: any;
  onSearchInput() {
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout);
    }
    this.searchTimeout = setTimeout(() => {
      this.onSearchChange();
    }, 500); // 500ms delay
  }
}
