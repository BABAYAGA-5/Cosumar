import { Component, OnInit, OnDestroy, inject, ChangeDetectorRef } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { signal } from '@angular/core';
import { environment } from '../../../environments/environment';
import { SlicePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'CreationStage',
  standalone: true,
  imports: [SlicePipe, FormsModule],
  templateUrl: './CreationStage.html',
  styleUrl: './CreationStage.css'
})
export class CreationStage implements OnInit, OnDestroy {
  private http = inject(HttpClient);
  private cdr = inject(ChangeDetectorRef);
  private sanitizer = inject(DomSanitizer);

  // File upload properties
  selectedFile = signal<File | null>(null);
  isDragOver = false;
  isUploading = signal(false);
  uploadMessage = signal<{type: string, text: string, data?: any} | null>(null);
  
  // Extracted data properties
  extractedData = signal<{nom: string, prenom: string, cin: string, date_naissance: string} | null>(null);
  cvExtractedData = signal<{email: string, phone: string} | null>(null);
  
  // Computed properties for CV extracted data to ensure reactivity
  get cvEmail(): string {
    return this.cvExtractedData()?.email || '';
  }
  
  get cvPhone(): string {
    return this.cvExtractedData()?.phone || '';
  }
  
  stageData = signal<{nature: string, date_debut: string, date_fin: string} | null>({
    nature: '',
    date_debut: '',
    date_fin: ''
  });
  isSaving = signal(false);
  saveMessage = signal<{type: string, text: string} | null>(null);
  
  // CIN preview URL
  cinPreviewUrl = signal<string | null>(null);
  
  // Documents management
  documents = signal<{[key: string]: File | null}>({
    convention: null,
    cv: null,
    assurance: null,
    lettre_motivation: null
  });
  
  // CV preview and processing
  cvPreviewUrl = signal<string | null>(null);
  isCvProcessing = signal(false);
  cvProcessingMessage = signal<{type: string, text: string} | null>(null);
  isGeneratingPreview = signal(false);
  
  // Computed property for safe URL
  get safePreviewUrl(): SafeResourceUrl | null {
    const url = this.cvPreviewUrl();
    return url ? this.sanitizer.bypassSecurityTrustResourceUrl(url) : null;
  }
  
  documentDragStates = signal<{[key: string]: boolean}>({
    convention: false,
    cv: false,
    assurance: false,
    lettre_motivation: false
  });
  
  // Candidate selection
  candidateMethod = signal<'new' | 'existing'>('existing');
  candidatesList = signal<any[]>([]);
  selectedCandidate = signal<any | null>(null);
  isLoadingCandidates = signal(false);
  searchQuery = signal('');
  filteredCandidates = signal<any[]>([]);
  
  // Sujet selection
  selectedSujet = signal<any | null>(null);
  isLoadingSujets = signal(false);
  sujetSearchQuery = signal('');
  filteredSujets = signal<any[]>([]);
  
  // Add debounce timer properties
  private searchDebounceTimer: any = null;
  private sujetSearchDebounceTimer: any = null;

    ngOnInit(): void {
    // Component initialization
  }

  ngOnDestroy(): void {
    // Clean up debounce timers on component destroy
    if (this.searchDebounceTimer) {
      clearTimeout(this.searchDebounceTimer);
    }
    if (this.sujetSearchDebounceTimer) {
      clearTimeout(this.sujetSearchDebounceTimer);
    }
    
    // Clean up blob URLs to prevent memory leaks
    if (this.cinPreviewUrl()) {
      URL.revokeObjectURL(this.cinPreviewUrl()!);
    }
    if (this.cvPreviewUrl()) {
      URL.revokeObjectURL(this.cvPreviewUrl()!);
    }
  }

  // File handling methods
  onFileSelected(event: Event): void {
    const target = event.target as HTMLInputElement;
    const files = target.files;
    if (files && files.length > 0) {
      this.selectedFile.set(files[0]);
      this.uploadMessage.set(null);
      this.generatePreviewUrl(files[0]);
      this.uploadCIN();
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;
  }

  onFileDropped(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;
    
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (this.isValidFileType(file)) {
        this.selectedFile.set(file);
        this.uploadMessage.set(null);
        this.generatePreviewUrl(file);
        this.uploadCIN();
      } else {
        this.uploadMessage.set({
          type: 'error',
          text: 'Type de fichier non autorisé. Veuillez télécharger JPG, JPEG ou PNG.'
        });
      }
    }
  }

  private isValidFileType(file: File): boolean {
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    return allowedTypes.includes(file.type);
  }

  private generatePreviewUrl(file: File): void {
    if (file) {
      const url = URL.createObjectURL(file);
      this.cinPreviewUrl.set(url);
    }
  }

  private async generateCvPreview(file: File): Promise<void> {
    if (!file) return;
    
    // Create a preview URL for viewing/downloading
    const url = URL.createObjectURL(file);
    this.cvPreviewUrl.set(url);
  }
  


  private async processCv(file: File): Promise<void> {
    this.isCvProcessing.set(true);
    this.cvProcessingMessage.set(null);

    try {
      const formData = new FormData();
      formData.append('cv', file);

      const response = await this.http.post<any>(
        `${environment.apiUrl}resume/process_cv/`,
        formData,
        { 
          headers: new HttpHeaders({
            'Authorization': `Bearer ${localStorage.getItem('access')}`
          })
        }
      ).toPromise();

      if (response && response.data) {
        this.cvExtractedData.set({
          email: response.data.email || '',
          phone: response.data.phone || ''
        });
        this.cvProcessingMessage.set({
          type: 'success',
          text: 'CV traité avec succès! Email et téléphone extraits.'
        });
        // Force change detection and input update
        this.cdr.detectChanges();
        this.forceInputUpdate();
      } else {
        // Set empty data to show the form even if no data was extracted
        this.cvExtractedData.set({
          email: '',
          phone: ''
        });
        this.cvProcessingMessage.set({
          type: 'success',
          text: 'CV traité avec succès! Vous pouvez saisir les informations manuellement.'
        });
        // Force change detection
        this.cdr.detectChanges();
      }

    } catch (error: any) {
      console.error('Error processing CV:', error);
      // Set empty data to show the form even on error
      this.cvExtractedData.set({
        email: '',
        phone: ''
      });
      this.cvProcessingMessage.set({
        type: 'error',
        text: error.error?.error || 'Erreur lors du traitement du CV. Vous pouvez saisir les informations manuellement.'
      });
      // Force change detection
      this.cdr.detectChanges();
    } finally {
      this.isCvProcessing.set(false);
    }
  }

  removeFile(): void {
    const currentUrl = this.cinPreviewUrl();
    if (currentUrl) {
      URL.revokeObjectURL(currentUrl);
      this.cinPreviewUrl.set(null);
    }
    
    this.selectedFile.set(null);
    this.uploadMessage.set(null);
    this.extractedData.set(null);
    this.saveMessage.set(null);
  }

  getFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  async uploadCIN(): Promise<void> {
    if (!this.selectedFile()) {
      this.uploadMessage.set({
        type: 'error',
        text: 'Veuillez sélectionner un fichier CIN.'
      });
      return;
    }

    this.isUploading.set(true);
    this.uploadMessage.set(null);
    this.extractedData.set(null);

    try {
      const formData = new FormData();
      formData.append('cin', this.selectedFile()!);

      const response = await this.http.post<any>(
        `${environment.apiUrl}resume/scan_cin/`,
        formData,
        { 
          headers: new HttpHeaders({
            'Authorization': `Bearer ${localStorage.getItem('access')}`
          })
        }
      ).toPromise();

      if (response.data) {
        this.extractedData.set({
          nom: response.data.nom || '',
          prenom: response.data.prenom || '',
          cin: response.data.cin || '',
          date_naissance: response.data.date_naissance || ''
        });
        this.uploadMessage.set(null);
      } else {
        this.uploadMessage.set({
          type: 'error',
          text: 'Aucune donnée extraite du CIN.'
        });
      }

    } catch (error: any) {
      console.error('Error scanning CIN:', error);
      this.uploadMessage.set({
        type: 'error',
        text: error.error?.error || 'Erreur lors du scan du CIN.'
      });
    } finally {
      this.isUploading.set(false);
    }
  }

  updateExtractedData(field: string, event: Event): void {
    // Prevent modification when using existing candidate
    if (this.candidateMethod() === 'existing') {
      return;
    }
    
    const target = event.target as HTMLInputElement | HTMLTextAreaElement;
    const value = target.value;
    
    this.extractedData.update(data => {
      if (!data) return null;
      return {
        ...data,
        [field]: value
      };
    });
  }

  updateCvExtractedData(field: string, event: Event): void {
    const target = event.target as HTMLInputElement | HTMLTextAreaElement;
    const value = target.value;
    
    this.cvExtractedData.update(data => {
      if (!data) return { email: '', phone: '' };
      return {
        ...data,
        [field]: value
      };
    });

    // Trigger change detection to update button validation
    this.cdr.detectChanges();
  }

  updateStageData(field: string, event: Event): void {
    const target = event.target as HTMLInputElement | HTMLSelectElement;
    const value = target.value;
    
    this.stageData.update(data => {
      if (!data) return { nature: '', date_debut: '', date_fin: '' };
      return {
        ...data,
        [field]: value
      };
    });
  }

  setCandidateMethod(method: 'new' | 'existing'): void {
    this.candidateMethod.set(method);
    
    if (method === 'existing') {
      this.removeFile();
      this.loadCandidates();
    } else {
      // Clear any existing candidate data
      this.selectedCandidate.set(null);
      this.extractedData.set(null);
      this.cvExtractedData.set(null);
      this.searchQuery.set('');
      this.filteredCandidates.set([]);
      
      // Clear CIN preview URL and uploaded file
      const currentCinUrl = this.cinPreviewUrl();
      if (currentCinUrl) {
        URL.revokeObjectURL(currentCinUrl);
        this.cinPreviewUrl.set(null);
      }
      this.selectedFile.set(null);
      
      // Clear CV preview and data
      const currentCvUrl = this.cvPreviewUrl();
      if (currentCvUrl) {
        URL.revokeObjectURL(currentCvUrl);
        this.cvPreviewUrl.set(null);
      }
      
      // Clear upload messages
      this.uploadMessage.set(null);
      this.cvProcessingMessage.set(null);
      
      // Reset documents
      this.documents.set({
        convention: null,
        cv: null,
        assurance: null,
        lettre_motivation: null
      });
    }
  }

  async loadCandidates(): Promise<void> {
    this.isLoadingCandidates.set(true);
    
    try {
      const response = await this.http.get<any>(
        `${environment.apiUrl}resume/chercher_stagiaires/`,
        { 
          headers: new HttpHeaders({
            'Authorization': `Bearer ${localStorage.getItem('access')}`
          })
        }
      ).toPromise();

      this.candidatesList.set(response.candidats || []);
    } catch (error: any) {
      console.error('Error loading candidates:', error);
      this.candidatesList.set([]);
    } finally {
      this.isLoadingCandidates.set(false);
    }
  }

  onSearchQueryChange(event: Event): void {
    const target = event.target as HTMLInputElement;
    const query = target.value.trim();
    this.searchQuery.set(query);
    
    if (this.searchDebounceTimer) {
      clearTimeout(this.searchDebounceTimer);
    }
    
    this.isLoadingCandidates.set(true);
    
    this.searchDebounceTimer = setTimeout(() => {
      this.searchCandidates(query);
    }, 500);
  }

  async searchCandidates(query: string): Promise<void> {
    try {
      const response = await this.http.get<any[]>(
        `${environment.apiUrl}resume/chercher_stagiaires/?search=${encodeURIComponent(query)}`,
        { 
          headers: new HttpHeaders({
            'Authorization': `Bearer ${localStorage.getItem('access')}`
          })
        }
      ).toPromise();

      this.filteredCandidates.set(response || []);
    } catch (error: any) {
      console.error('Error searching candidates:', error);
      this.filteredCandidates.set([]);
    } finally {
      this.isLoadingCandidates.set(false);
    }
  }

  selectCandidate(candidate: any): void {
    this.selectedCandidate.set(candidate);
    this.searchQuery.set(`${candidate.prenom} ${candidate.nom} (${candidate.matricule})`);
    this.filteredCandidates.set([]);
    
    this.extractedData.set({
      nom: candidate.nom || '',
      prenom: candidate.prenom || '',
      cin: candidate.matricule || '',
      date_naissance: candidate.date_naissance || ''
    });

    // Fetch candidate's documents from latest stage
    this.fetchCandidateDocuments(candidate.matricule);
  }

  async fetchCandidateDocuments(matricule: string): Promise<void> {
    try {
      const response = await this.http.get<any>(
        `${environment.apiUrl}resume/get_candidate_documents/${matricule}/`,
        {
          headers: new HttpHeaders({
            'Authorization': `Bearer ${localStorage.getItem('access')}`
          })
        }
      ).toPromise();

      if (response && response.success) {
        console.log('Fetching candidate documents:', response);

        // Set CV extracted data if available
        if (response.cv_data) {
          this.cvExtractedData.set({
            email: response.cv_data.email || '',
            phone: response.cv_data.phone || ''
          });
        }

        // Download and set up the actual files
        const docs: any = {};
        
        if (response.documents.has_cv) {
          try {
            // Download CV file as blob using get_stage_document
            const cvBlob = await this.http.get(
              `${environment.apiUrl}resume/get_stage_document/${response.stage_id}/cv/`,
              {
                headers: new HttpHeaders({
                  'Authorization': `Bearer ${localStorage.getItem('access')}`
                }),
                responseType: 'blob'
              }
            ).toPromise();

            if (cvBlob) {
              // Create a proper File object from the blob
              const cvFile = new File([cvBlob], response.documents.cv_file, { type: 'application/pdf' });
              docs['cv'] = cvFile;
              
              // Generate preview using the new method
              console.log('Generating preview for fetched CV file'); // Debug log
              await this.generateCvPreview(cvFile);
            }
          } catch (error) {
            console.error('Error downloading CV file:', error);
          }
        }

        if (response.documents.has_cin) {
          try {
            // Download CIN file as blob using get_cin with matricule
            const cinBlob = await this.http.get(
              `${environment.apiUrl}resume/get_cin/${matricule}/`,
              {
                headers: new HttpHeaders({
                  'Authorization': `Bearer ${localStorage.getItem('access')}`
                }),
                responseType: 'blob'
              }
            ).toPromise();

            if (cinBlob) {
              // Create a proper File object from the blob
              const cinFile = new File([cinBlob], response.documents.cin_file, { type: 'image/jpeg' });
              this.selectedFile.set(cinFile);
              
              // Create URL for preview
              const cinUrl = URL.createObjectURL(cinBlob);
              this.cinPreviewUrl.set(cinUrl);
            }
          } catch (error) {
            console.error('Error downloading CIN file:', error);
          }
        }

        // Update documents signal
        console.log('Updating documents signal with:', docs); // Debug log
        this.documents.update(currentDocs => ({
          ...currentDocs,
          ...docs
        }));
        console.log('Documents signal after update:', this.documents()); // Debug log

        // Trigger change detection
        this.cdr.detectChanges();
        
        console.log('Successfully loaded candidate documents');
        console.log('Current CV preview URL:', this.cvPreviewUrl()); // Debug log
      }
    } catch (error) {
      console.error('Error fetching candidate documents:', error);
      // Don't show error to user as this is not critical
    }
  }

  clearCandidateSelection(): void {
    this.selectedCandidate.set(null);
    this.searchQuery.set('');
    this.filteredCandidates.set([]);
    this.extractedData.set(null);
    
    // Clear fetched documents and preview URLs
    this.cvExtractedData.set(null);
    this.selectedFile.set(null);
    
    // Clean up blob URLs to prevent memory leaks
    if (this.cinPreviewUrl()) {
      URL.revokeObjectURL(this.cinPreviewUrl()!);
    }
    if (this.cvPreviewUrl()) {
      URL.revokeObjectURL(this.cvPreviewUrl()!);
    }
    
    this.cinPreviewUrl.set(null);
    this.cvPreviewUrl.set(null);
    
    // Clear CV document from documents
    this.documents.update(docs => ({
      ...docs,
      cv: null
    }));
  }

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
    }, 500);
  }

  async searchSujets(query: string): Promise<void> {
    try {
      const response = await this.http.get<any[]>(
        `${environment.apiUrl}resume/chercher_sujets/?search=${encodeURIComponent(query)}`,
        { 
          headers: new HttpHeaders({
            'Authorization': `Bearer ${localStorage.getItem('access')}`
          })
        }
      ).toPromise();

      this.filteredSujets.set(response || []);
    } catch (error: any) {
      console.error('Error searching sujets:', error);
      this.filteredSujets.set([]);
    } finally {
      this.isLoadingSujets.set(false);
    }
  }

  selectSujet(sujet: any): void {
    this.selectedSujet.set(sujet);
    this.sujetSearchQuery.set(`${sujet.titre}`);
    this.filteredSujets.set([]);
  }

  clearSujetSelection(): void {
    this.selectedSujet.set(null);
    this.sujetSearchQuery.set('');
    this.filteredSujets.set([]);
  }

  canCreateStage(): boolean {
    const data = this.extractedData();
    const cvData = this.cvExtractedData();
    const docs = this.documents();
    const stage = this.stageData();
    
    // Check if candidate data is complete (CIN data)
    const hasCandidateData = !!(data?.nom && data?.prenom && data?.cin);
    
    // Check if CV data is complete (email and phone when CV is uploaded)
    // Allow creation even if CV data is not fully extracted yet
    const hasCvData = docs['cv'] ? true : true;
    
    // Check if required files are uploaded
    const hasRequiredFiles = this.candidateMethod() === 'existing' ? 
      docs['cv'] : 
      (docs['cv'] && this.selectedFile());
    
    // Check if stage data is complete (including sujet)
    const hasStageData = !!(stage?.nature && stage?.date_debut && stage?.date_fin && this.selectedSujet());
    
    return !!(
      hasCandidateData &&
      hasCvData &&
      hasRequiredFiles &&
      hasStageData
    );
  }

  canCompleteStage(): boolean {
    const data = this.extractedData();
    const cvData = this.cvExtractedData();
    const docs = this.documents();
    const stage = this.stageData();
    
    // Check if candidate data is complete (CIN data)
    const hasCandidateData = !!(data?.nom && data?.prenom && data?.cin);
    
    // Check if CV data is complete (email and phone when CV is uploaded)
    // Allow completion even if CV data is not fully extracted yet
    const hasCvData = docs['cv'] ? true : true;
    
    // Check if all required files are uploaded
    const hasRequiredFiles = this.candidateMethod() === 'existing' ? 
      (docs['cv'] && docs['convention'] && docs['assurance']) :
      (docs['cv'] && docs['convention'] && docs['assurance'] && this.selectedFile());
    
    // Check if stage data is complete (including sujet)
    const hasStageData = !!(stage?.nature && stage?.date_debut && stage?.date_fin && this.selectedSujet());
    
    return !!(
      hasCandidateData &&
      hasCvData &&
      hasRequiredFiles &&
      hasStageData
    );
  }

  shouldShowActions(): boolean {
    // Show actions if any of these conditions are met:
    // 1. An existing candidate is selected
    // 2. A new candidate has been scanned (extractedData exists)
    // 3. Any stage data has been entered
    // 4. Any documents have been uploaded
    
    const hasSelectedCandidate = this.candidateMethod() === 'existing' && this.selectedCandidate();
    const hasExtractedData = this.extractedData();
    const hasStageData = this.stageData() && (
      this.stageData()!.nature || 
      this.stageData()!.date_debut || 
      this.stageData()!.date_fin
    );
    const hasDocuments = Object.values(this.documents()).some(doc => doc !== null);
    const hasSelectedSujet = this.selectedSujet();
    
    return !!(
      hasSelectedCandidate || 
      hasExtractedData || 
      hasStageData || 
      hasDocuments || 
      hasSelectedSujet
    );
  }

  async createStage(): Promise<void> {
    if (!this.canCreateStage()) {
      this.saveMessage.set({
        type: 'error',
        text: 'Documents minimum requis : candidat sélectionné, CV téléchargé et informations de stage complètes.'
      });
      return;
    }

    this.isSaving.set(true);
    this.saveMessage.set(null);

    try {
      const data = this.extractedData()!;
      const cvData = this.cvExtractedData();
      const docs = this.documents();
      const stage = this.stageData()!;
      
      let matricule: string;
      
      if (this.candidateMethod() === 'new') {
        // Step 1: Create the new stagiaire first
        const stagiaireFormData = new FormData();
        stagiaireFormData.append('nom', data.nom);
        stagiaireFormData.append('prenom', data.prenom);
        stagiaireFormData.append('cin', data.cin);
        stagiaireFormData.append('date_naissance', data.date_naissance);
        stagiaireFormData.append('email', cvData?.email || '');
        stagiaireFormData.append('phone', cvData?.phone || '');
        
        if (this.selectedFile()) {
          stagiaireFormData.append('cin_file', this.selectedFile()!);
        }

        const stagiaireResponse = await this.http.post<any>(
          `${environment.apiUrl}resume/enregistrer_stagiaire/`,
          stagiaireFormData,
          { 
            headers: new HttpHeaders({
              'Authorization': `Bearer ${localStorage.getItem('access')}`
            })
          }
        ).toPromise();
        
        matricule = stagiaireResponse.matricule;
      } else {
        // For existing stagiaire, use the selected candidate's matricule
        const selectedCandidate = this.selectedCandidate()!;
        matricule = selectedCandidate.matricule;
      }
      
      // Step 2: Create the stage for the stagiaire (both new and existing)
      const stageFormData = new FormData();
      stageFormData.append('matricule', matricule);
      stageFormData.append('nature', stage.nature);
      stageFormData.append('date_debut', stage.date_debut);
      stageFormData.append('date_fin', stage.date_fin);
      
      if (this.selectedSujet()) {
        stageFormData.append('sujet_id', this.selectedSujet()!.id.toString());
      }

      if (docs['cv']) stageFormData.append('cv_file', docs['cv']);
      if (docs['convention']) stageFormData.append('convention_file', docs['convention']);
      if (docs['assurance']) stageFormData.append('assurance_file', docs['assurance']);
      if (docs['lettre_motivation']) stageFormData.append('lettre_motivation_file', docs['lettre_motivation']);

      const stageResponse = await this.http.post<any>(
        `${environment.apiUrl}resume/creer_stage/`,
        stageFormData,
        { 
          headers: new HttpHeaders({
            'Authorization': `Bearer ${localStorage.getItem('access')}`
          })
        }
      ).toPromise();

      this.saveMessage.set({
        type: 'success',
        text: this.candidateMethod() === 'new' ? 
          'Nouveau stagiaire créé et stage créé avec succès! Vous pouvez maintenant ajouter les documents manquants pour compléter le dossier.' :
          'Stage créé avec succès! Vous pouvez maintenant ajouter les documents manquants pour compléter le dossier.'
      });

    } catch (error: any) {
      console.error('Error creating stage:', error);
      this.saveMessage.set({
        type: 'error',
        text: error.error?.error || 'Erreur lors de la création du stage.'
      });
    } finally {
      this.isSaving.set(false);
    }
  }

  async completeStage(): Promise<void> {
    if (!this.canCompleteStage()) {
      this.saveMessage.set({
        type: 'error',
        text: 'Tous les documents obligatoires et informations de stage sont requis pour compléter le dossier.'
      });
      return;
    }

    this.isSaving.set(true);
    this.saveMessage.set(null);

    try {
      const data = this.extractedData()!;
      const cvData = this.cvExtractedData();
      const docs = this.documents();
      const stage = this.stageData()!;
      
      let matricule: string;
      
      if (this.candidateMethod() === 'new') {
        // Step 1: Create the new stagiaire first (if not already created)
        const stagiaireFormData = new FormData();
        stagiaireFormData.append('nom', data.nom);
        stagiaireFormData.append('prenom', data.prenom);
        stagiaireFormData.append('cin', data.cin);
        stagiaireFormData.append('date_naissance', data.date_naissance);
        stagiaireFormData.append('email', cvData?.email || '');
        stagiaireFormData.append('phone', cvData?.phone || '');
        
        if (this.selectedFile()) {
          stagiaireFormData.append('cin_file', this.selectedFile()!);
        }

        // Try to create stagiaire (might already exist if createStage was called first)
        try {
          const stagiaireResponse = await this.http.post<any>(
            `${environment.apiUrl}resume/enregistrer_stagiaire/`,
            stagiaireFormData,
            { 
              headers: new HttpHeaders({
                'Authorization': `Bearer ${localStorage.getItem('access')}`
              })
            }
          ).toPromise();
          
          matricule = stagiaireResponse.matricule;
        } catch (error: any) {
          // If stagiaire already exists, use the CIN as matricule
          if (error.error?.error?.includes('existe déjà')) {
            matricule = data.cin;
          } else {
            throw error;
          }
        }
      } else {
        // For existing stagiaire, use the selected candidate's matricule
        const selectedCandidate = this.selectedCandidate()!;
        matricule = selectedCandidate.matricule;
      }
      
      // Step 2: Create the complete stage
      const stageFormData = new FormData();
      stageFormData.append('matricule', matricule);
      stageFormData.append('nature', stage.nature);
      stageFormData.append('date_debut', stage.date_debut);
      stageFormData.append('date_fin', stage.date_fin);
      stageFormData.append('status', 'dossier_complete');
      
      if (this.selectedSujet()) {
        stageFormData.append('sujet_id', this.selectedSujet()!.id.toString());
      }

      if (docs['cv']) stageFormData.append('cv_file', docs['cv']);
      if (docs['convention']) stageFormData.append('convention_file', docs['convention']);
      if (docs['assurance']) stageFormData.append('assurance_file', docs['assurance']);
      if (docs['lettre_motivation']) stageFormData.append('lettre_motivation_file', docs['lettre_motivation']);

      const stageResponse = await this.http.post<any>(
        `${environment.apiUrl}resume/creer_stage/`,
        stageFormData,
        { 
          headers: new HttpHeaders({
            'Authorization': `Bearer ${localStorage.getItem('access')}`
          })
        }
      ).toPromise();

      this.saveMessage.set({
        type: 'success',
        text: 'Dossier de stage complété avec succès! Le stagiaire peut maintenant commencer son stage.'
      });

      setTimeout(() => {
        this.resetForm();
      }, 3000);

    } catch (error: any) {
      console.error('Error completing stage dossier:', error);
      this.saveMessage.set({
        type: 'error',
        text: error.error?.error || 'Erreur lors de la finalisation du dossier de stage.'
      });
    } finally {
      this.isSaving.set(false);
    }
  }

  // Document handling methods
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
        
        // Handle CV specific processing
        if (documentType === 'cv') {
          await this.generateCvPreview(file);
          this.processCv(file);
        }
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
      console.log('Dropped file:', file.name, file.type); // Debug log
      if (this.isValidDocumentType(file)) {
        console.log('Dropped file is valid, updating documents'); // Debug log
        this.documents.update(docs => ({
          ...docs,
          [documentType]: file
        }));
        
        // Handle CV specific processing
        if (documentType === 'cv') {
          console.log('Processing dropped CV file'); // Debug log
          await this.generateCvPreview(file);
          this.processCv(file);
        }
      } else {
        console.log('Dropped file type not valid:', file.type); // Debug log
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
    // Clean up CV preview URL if removing CV
    if (documentType === 'cv') {
      const currentCvUrl = this.cvPreviewUrl();
      if (currentCvUrl) {
        URL.revokeObjectURL(currentCvUrl);
        this.cvPreviewUrl.set(null);
      }
      
      this.cvProcessingMessage.set(null);
      this.cvExtractedData.set(null);
    }
    
    this.documents.update(docs => ({
      ...docs,
      [documentType]: null
    }));
  }

  resetExtractedData(): void {
    this.extractedData.set(null);
    this.saveMessage.set(null);
  }

  // Temporary test method for debugging CV data
  testCvData(): void {
    this.cvExtractedData.set({
      email: 'test@example.com',
      phone: '+212 6 12 34 56 78'
    });
    this.cvProcessingMessage.set({
      type: 'success',
      text: 'Données de test ajoutées!'
    });
    // Force change detection and input update
    this.cdr.detectChanges();
    this.forceInputUpdate();
  }

  // Method to force input field updates
  private forceInputUpdate(): void {
    setTimeout(() => {
      const emailInput = document.getElementById('extracted-email') as HTMLInputElement;
      const phoneInput = document.getElementById('extracted-phone') as HTMLInputElement;
      
      if (emailInput && this.cvExtractedData()?.email) {
        emailInput.value = this.cvExtractedData()!.email;
      }
      if (phoneInput && this.cvExtractedData()?.phone) {
        phoneInput.value = this.cvExtractedData()!.phone;
      }
    }, 100);
  }

  resetForm(): void {
    if (this.searchDebounceTimer) {
      clearTimeout(this.searchDebounceTimer);
      this.searchDebounceTimer = null;
    }
    if (this.sujetSearchDebounceTimer) {
      clearTimeout(this.sujetSearchDebounceTimer);
      this.sujetSearchDebounceTimer = null;
    }
    
    const currentUrl = this.cinPreviewUrl();
    if (currentUrl) {
      URL.revokeObjectURL(currentUrl);
      this.cinPreviewUrl.set(null);
    }
    
    const currentCvUrl = this.cvPreviewUrl();
    if (currentCvUrl) {
      URL.revokeObjectURL(currentCvUrl);
      this.cvPreviewUrl.set(null);
    }
    
    this.selectedFile.set(null);
    this.uploadMessage.set(null);
    this.extractedData.set(null);
    this.cvExtractedData.set(null);
    this.saveMessage.set(null);
    this.selectedCandidate.set(null);
    this.candidateMethod.set('new');
    this.searchQuery.set('');
    this.filteredCandidates.set([]);
    this.selectedSujet.set(null);
    this.sujetSearchQuery.set('');
    this.filteredSujets.set([]);
    this.cvProcessingMessage.set(null);
    
    this.stageData.set({
      nature: '',
      date_debut: '',
      date_fin: ''
    });
    
    this.documents.set({
      convention: null,
      cv: null,
      assurance: null,
      lettre_motivation: null
    });
    
    this.documentDragStates.set({
      convention: false,
      cv: false,
      assurance: false,
      lettre_motivation: false
    });
  }
}
