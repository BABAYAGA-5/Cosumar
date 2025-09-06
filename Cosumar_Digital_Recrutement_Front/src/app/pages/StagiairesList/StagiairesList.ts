import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-stagiaires-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './StagiairesList.html',
  styleUrls: ['./StagiairesList.css']
})
export class StagiairesList implements OnInit {
  stagiaires: any[] = [];
  loading = true;
  error: string | null = null;
  
  // Pagination properties
  currentPage = 1;
  pageSize = 25;
  totalCount = 0;
  totalPages = 0;
  hasNext = false;
  hasPrevious = false;
  nextPageNumber: number | null = null;
  previousPageNumber: number | null = null;
  
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

    const url = `${this.apiUrl}?page=${this.currentPage}&page_size=${this.pageSize}`;

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
      'en_attente_signature_de_l_encadrant': 'En attente de signature de l\'encadrant',
      'en_attente_signature_du_responsable_RH': 'En attente de signature du responsable RH',
      'en_attente_signature_du_stagiaire': 'En attente de signature du stagiaire',
      'stage_en_cours': 'Stage en cours',
      'en_attente_depot_rapport': 'En attente de dépôt de rapport',
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
}
