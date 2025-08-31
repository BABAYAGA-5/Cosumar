import { Component, OnInit, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ActivatedRoute, Router } from '@angular/router';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { signal } from '@angular/core';
import { environment } from '../../../environments/environment';

interface StagiaireData {
  matricule: string;
  prenom: string;
  nom: string;
  email?: string;
  num_tel?: string;
  date_naissance?: string;
}

interface SujetData {
  id: number;
  titre: string;
  description: string;
}

interface StageData {
  id: number;
  nature: string;
  statut: string;
  date_debut: string;
  date_fin: string;
  prolongation: string | null;
  created_at: string;
  updated_at: string;
  stagiaire: StagiaireData;
  sujet?: SujetData;
}

@Component({
  selector: 'StageDetails',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './StageDetails.html',
  styleUrl: './StageDetails.css'
})
export class StageDetails implements OnInit, OnDestroy {
  private http = inject(HttpClient);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private sanitizer = inject(DomSanitizer);
  private cdr = inject(ChangeDetectorRef);

  // Stage data - using the simpler interface
  stageData = signal<StageData | null>(null);
  isLoading = signal(true);
  errorMessage = signal<string | null>(null);
  
  // File previews
  cinPreviewUrl = signal<SafeResourceUrl | null>(null);
  cvPreviewUrl = signal<SafeResourceUrl | null>(null);
  conventionPreviewUrl = signal<SafeResourceUrl | null>(null);
  assurancePreviewUrl = signal<SafeResourceUrl | null>(null);
  lettreMotivationPreviewUrl = signal<SafeResourceUrl | null>(null);
  demandeStagePreviewUrl = signal<SafeResourceUrl | null>(null);

  // UI state
  isEditMode = signal(false);
  isSaving = signal(false);
  isUploading = signal(false);

  // Document upload state (like CreationStage)
  documents = signal<{[key: string]: File | null}>({
    convention: null,
    assurance: null,
    lettre_motivation: null,
    demande_de_stage: null,
    cv: null
  });

  documentDragStates = signal<{[key: string]: boolean}>({
    convention: false,
    assurance: false,
    lettre_motivation: false,
    demande_de_stage: false,
    cv: false
  });

  // Sujet selection (like CreationStage)
  selectedSujet = signal<SujetData | null>(null);
  isLoadingSujets = signal(false);
  sujetSearchQuery = signal('');
  filteredSujets = signal<SujetData[]>([]);
  private sujetSearchDebounceTimer: any = null;

  // File upload state (legacy - keeping for compatibility)
  selectedFiles = signal<{ [key: string]: File }>({});
  uploadProgress = signal<{ [key: string]: number }>({
    convention: 0,
    assurance: 0,
    lettre_motivation: 0,
    demande_de_stage: 0
  });

  ngOnInit(): void {
    this.route.params.subscribe(params => {
      const stageId = params['stageId'] || params['id'];
      console.log('StageDetails ngOnInit - Stage ID:', stageId);
      console.log('Route params:', params);
      
      if (stageId) {
        this.loadStageById(stageId);
      } else {
        this.errorMessage.set('ID du stage manquant');
        this.isLoading.set(false);
      }
    });
  }

  ngOnDestroy(): void {
    // Clean up any object URLs
    this.cleanupPreviewUrls();
    
    // Clean up debounce timer
    if (this.sujetSearchDebounceTimer) {
      clearTimeout(this.sujetSearchDebounceTimer);
    }
  }

  private cleanupPreviewUrls(): void {
    const urls = [
      this.cinPreviewUrl(),
      this.cvPreviewUrl(),
      this.conventionPreviewUrl(),
      this.assurancePreviewUrl(),
      this.lettreMotivationPreviewUrl(),
      this.demandeStagePreviewUrl()
    ];

    urls.forEach(url => {
      if (url && typeof url === 'string') {
        URL.revokeObjectURL(url);
      }
    });
  }

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access');
    console.log('Token for request:', token ? 'Token present' : 'No token found');
    
    if (!token) {
      console.log('No authentication token found - redirecting to login');
      this.router.navigate(['/login'], { replaceUrl: true });
      return new HttpHeaders();
    }
    
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }

  private loadStageById(stage_id: string): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.http.get<{success: boolean, data: StageData}>(`${environment.apiUrl}resume/recuperer_stage/${stage_id}/`, {
      headers: this.getAuthHeaders()
    }).subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.stageData.set(response.data);
          
          // Initialize sujet selection state
          if (response.data.sujet) {
            this.selectedSujet.set(response.data.sujet);
          }
          
          this.loadDocumentPreviews(response.data);
          this.isLoading.set(false);
        } else {
          this.errorMessage.set('Aucune donnée trouvée pour ce stage');
          this.isLoading.set(false);
        }
      },
      error: (error) => {
        console.error('Error loading stage details:', error);
        
        // Check if it's an authentication error
        if (error.status === 401 || error.status === 403) {
          console.log('Authentication error - redirecting to login');
          localStorage.clear(); // Clear expired tokens
          this.router.navigate(['/login'], { replaceUrl: true });
          return;
        }
        
        this.errorMessage.set('Erreur lors du chargement des détails du stage');
        this.isLoading.set(false);
      }
    });
  }

  private loadDocumentPreviews(stageData: StageData): void {
    // Load CIN if available
    if (stageData.stagiaire.matricule) {
      this.loadDocument('cin', stageData.stagiaire.matricule);
    }

    // Load other documents - we'll try to load them and handle errors gracefully
    const stageId = stageData.id.toString();
    this.loadDocument('cv', stageId);
    this.loadDocument('convention', stageId);
    this.loadDocument('assurance', stageId);
    this.loadDocument('lettre_motivation', stageId);
    this.loadDocument('demande_de_stage', stageId);
  }

  private loadDocument(type: string, id: string): void {
    const url = type === 'cin' 
      ? `${environment.apiUrl}resume/get_cin/${id}/`
      : `${environment.apiUrl}resume/get_stage_document/${id}/${type}/`;

    this.http.get(url, {
      headers: this.getAuthHeaders(),
      responseType: 'blob'
    }).subscribe({
      next: (blob) => {
        const objectUrl = URL.createObjectURL(blob);
        const safeUrl = this.sanitizer.bypassSecurityTrustResourceUrl(objectUrl);
        
        switch (type) {
          case 'cin':
            this.cinPreviewUrl.set(safeUrl);
            break;
          case 'cv':
            this.cvPreviewUrl.set(safeUrl);
            break;
          case 'convention':
            this.conventionPreviewUrl.set(safeUrl);
            break;
          case 'assurance':
            this.assurancePreviewUrl.set(safeUrl);
            break;
          case 'lettre_motivation':
            this.lettreMotivationPreviewUrl.set(safeUrl);
            break;
          case 'demande_de_stage':
            this.demandeStagePreviewUrl.set(safeUrl);
            break;
        }
      },
      error: (error) => {
        console.error(`Error loading ${type}:`, error);
      }
    });
  }

  toggleEditMode(): void {
    this.isEditMode.set(!this.isEditMode());
  }

  updateStageData(field: string, event: any): void {
    const stageData = this.stageData();
    if (!stageData) return;

    const target = event.target || event;
    const value = target.value || target;

    const updatedStageData = { ...stageData };
    
    if (field.includes('.')) {
      const [section, child] = field.split('.');
      
      if (section === 'stagiaire') {
        updatedStageData.stagiaire = {
          ...updatedStageData.stagiaire,
          [child]: value
        };
      } else if (section === 'sujet' && updatedStageData.sujet) {
        updatedStageData.sujet = {
          ...updatedStageData.sujet,
          [child]: value
        };
      }
    } else {
      // Direct field update for stage properties
      (updatedStageData as any)[field] = value;
    }

    this.stageData.set(updatedStageData);
  }

  saveChanges(): void {
    const stageData = this.stageData();
    if (!stageData) return;

    this.isSaving.set(true);

    // Prepare data for update API (send only editable fields)
    const updateData: any = {
      nature: stageData.nature,
      date_debut: stageData.date_debut,
      date_fin: stageData.date_fin,
      statut: stageData.statut,
      prolongation: stageData.prolongation,
      stagiaire: {
        nom: stageData.stagiaire.nom,
        prenom: stageData.stagiaire.prenom,
        email: stageData.stagiaire.email,
        num_tel: stageData.stagiaire.num_tel,
        date_naissance: stageData.stagiaire.date_naissance
      }
    };

    // Include sujet data if it exists
    if (stageData.sujet) {
      updateData.sujet_id = stageData.sujet.id;
    }

    this.http.put(`${environment.apiUrl}resume/update_stage/${stageData.id}/`, updateData, {
      headers: this.getAuthHeaders()
    }).subscribe({
      next: (response) => {
        this.isSaving.set(false);
        this.isEditMode.set(false);
        // Reload stage details to get updated data
        this.loadStageById(stageData.id.toString());
        console.log('Stage updated successfully');
      },
      error: (error) => {
        console.error('Error updating stage:', error);
        this.isSaving.set(false);
        // Show error message
      }
    });
  }

  cancelEdit(): void {
    this.isEditMode.set(false);
    // Reload original data
    const stageData = this.stageData();
    if (stageData) {
      this.loadStageById(stageData.id.toString());
    }
  }

  goBack(): void {
    this.router.navigate(['/dashboardpage/stages']);
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

  getStatusColor(statut: string): string {
    const statusColors: { [key: string]: string } = {
      'annule': '#ef4444',
      'en_attente_depot_dossier': '#f59e0b',
      'expire': '#dc2626',
      'en_attente_visite_medicale': '#3b82f6',
      'en_attente_des_signatures': '#8b5cf6',
      'stage_en_cours': '#10b981',
      'en_attente_depot_rapport': '#06b6d4',
      'en_attente_signature_du_rapport_par_l_encadrant': '#8b5cf6',
      'termine': '#22c55e'
    };
    return statusColors[statut] || '#6b7280';
  }

  // Sujet selection methods
  onSujetSearchQueryChange(event: Event): void {
    const target = event.target as HTMLInputElement;
    const query = target.value.trim();
    this.sujetSearchQuery.set(query);

    if (this.sujetSearchDebounceTimer) {
      clearTimeout(this.sujetSearchDebounceTimer);
    }

    this.isLoadingSujets.set(true);

    this.sujetSearchDebounceTimer = setTimeout(() => {
      this.searchSujets(query);
    }, 300);
  }

  async searchSujets(query: string): Promise<void> {
    try {
      const response = await this.http.get<SujetData[]>(
        `${environment.apiUrl}resume/chercher_sujets/?search=${encodeURIComponent(query)}`,
        {
          headers: this.getAuthHeaders()
        }
      ).toPromise();

      this.filteredSujets.set(response || []);
    } catch (error) {
      console.error('Error searching sujets:', error);
      this.filteredSujets.set([]);
    } finally {
      this.isLoadingSujets.set(false);
    }
  }

  selectSujet(sujet: SujetData): void {
    // Update the stage data with the selected sujet
    const stageData = this.stageData();
    if (stageData) {
      const updatedStageData = { ...stageData, sujet };
      this.stageData.set(updatedStageData);
    }
    
    // Update UI state
    this.selectedSujet.set(sujet);
    this.sujetSearchQuery.set(`${sujet.titre}`);
    this.filteredSujets.set([]);
  }

  clearSujetSelection(): void {
    // Remove sujet from stage data
    const stageData = this.stageData();
    if (stageData) {
      const updatedStageData = { ...stageData };
      delete updatedStageData.sujet;
      this.stageData.set(updatedStageData);
    }
    
    // Clear UI state
    this.selectedSujet.set(null);
    this.sujetSearchQuery.set('');
    this.filteredSujets.set([]);
  }

  // File upload methods
  onFileSelected(documentType: string, event: any): void {
    const file = event.target.files[0];
    if (file) {
      const currentFiles = this.selectedFiles();
      this.selectedFiles.set({
        ...currentFiles,
        [documentType]: file
      });
      console.log(`File selected for ${documentType}:`, file.name);
    }
  }

  hasSelectedFiles(): boolean {
    const files = this.selectedFiles();
    return Object.keys(files).length > 0;
  }

  clearSelectedFiles(): void {
    this.selectedFiles.set({});
    // Reset file inputs
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach((input: any) => {
      input.value = '';
    });
    
    // Reset progress
    this.uploadProgress.set({
      convention: 0,
      assurance: 0,
      lettre_motivation: 0,
      demande_de_stage: 0
    });
  }

  uploadSelectedFiles(): void {
    const files = this.selectedFiles();
    const stageData = this.stageData();
    
    if (!stageData || Object.keys(files).length === 0) {
      return;
    }

    this.isUploading.set(true);

    // Upload files one by one
    const documentTypes = Object.keys(files);
    let currentIndex = 0;

    const uploadNext = () => {
      if (currentIndex >= documentTypes.length) {
        // All files uploaded successfully
        this.isUploading.set(false);
        this.clearSelectedFiles();
        // Reload the stage data to refresh document previews
        this.loadStageById(stageData.id.toString());
        return;
      }

      const documentType = documentTypes[currentIndex];
      const file = files[documentType];
      
      this.uploadDocument(documentType, file, stageData.id).then(() => {
        currentIndex++;
        uploadNext();
      }).catch((error) => {
        console.error(`Error uploading ${documentType}:`, error);
        this.isUploading.set(false);
        // You can add error handling here
      });
    };

    uploadNext();
  }

  private uploadDocument(documentType: string, file: File, stageId: number): Promise<void> {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append(documentType, file);

      // Update progress
      const currentProgress = this.uploadProgress();
      this.uploadProgress.set({
        ...currentProgress,
        [documentType]: 0
      });

      this.http.put(`${environment.apiUrl}resume/upload_stage_document/${stageId}/`, formData, {
        headers: new HttpHeaders({
          'Authorization': `Bearer ${localStorage.getItem('access')}`
        }),
        reportProgress: true,
        observe: 'events'
      }).subscribe({
        next: (event: any) => {
          if (event.type === 1) { // UploadProgress
            const progress = Math.round(100 * event.loaded / event.total);
            const currentProgress = this.uploadProgress();
            this.uploadProgress.set({
              ...currentProgress,
              [documentType]: progress
            });
          } else if (event.type === 4) { // Response
            const currentProgress = this.uploadProgress();
            this.uploadProgress.set({
              ...currentProgress,
              [documentType]: 100
            });
            resolve();
          }
        },
        error: (error) => {
          reject(error);
        }
      });
    });
  }

  // New document handling methods (like CreationStage)
  async onDocumentSelected(event: Event, documentType: string): Promise<void> {
    const target = event.target as HTMLInputElement;
    const files = target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (this.isValidDocumentType(file)) {
        this.documents.update(docs => ({
          ...docs,
          [documentType]: file
        }));
        console.log(`Document selected for ${documentType}:`, file.name);
      }
    }
  }

  onDocumentDragOver(event: DragEvent, documentType: string): void {
    event.preventDefault();
    this.documentDragStates.update(states => ({
      ...states,
      [documentType]: true
    }));
  }

  onDocumentDragLeave(event: DragEvent, documentType: string): void {
    event.preventDefault();
    this.documentDragStates.update(states => ({
      ...states,
      [documentType]: false
    }));
  }

  async onDocumentDropped(event: DragEvent, documentType: string): Promise<void> {
    event.preventDefault();
    this.documentDragStates.update(states => ({
      ...states,
      [documentType]: false
    }));
    
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (this.isValidDocumentType(file)) {
        this.documents.update(docs => ({
          ...docs,
          [documentType]: file
        }));
        console.log(`Document dropped for ${documentType}:`, file.name);
      }
    }
  }

  private isValidDocumentType(file: File): boolean {
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    return allowedTypes.includes(file.type);
  }

  removeDocument(documentType: string): void {
    this.documents.update(docs => ({
      ...docs,
      [documentType]: null
    }));
    
    // Clear the file input
    const fileInputs = document.querySelectorAll(`input[type="file"]`);
    fileInputs.forEach((input: any) => {
      if (input.accept === '.pdf,.doc,.docx') {
        input.value = '';
      }
    });
  }

  hasDocumentsToUpload(): boolean {
    const docs = this.documents();
    return Object.values(docs).some(doc => doc !== null);
  }

  async uploadDocuments(): Promise<void> {
    const docs = this.documents();
    const stageData = this.stageData();
    
    if (!stageData) {
      console.error('No stage data available');
      return;
    }

    this.isUploading.set(true);
    
    try {
      for (const [docType, file] of Object.entries(docs)) {
        if (file) {
          await this.uploadDocument(docType, file, stageData.id);
        }
      }
      
      // Clear uploaded documents
      this.documents.set({
        convention: null,
        assurance: null,
        lettre_motivation: null,
        demande_de_stage: null
      });
      
      // Reload the stage to show updated documents
      this.loadStageById(stageData.id.toString());
      
      console.log('All documents uploaded successfully');
    } catch (error) {
      console.error('Error uploading documents:', error);
    } finally {
      this.isUploading.set(false);
    }
  }
}
