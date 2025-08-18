import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { signal } from '@angular/core';
import { environment } from '../../../environments/environment';
import { SlicePipe } from '@angular/common';

@Component({
  selector: 'app-creation-stage',
  standalone: true,
  imports: [SlicePipe],
  templateUrl: './CreationStage.html',
  styleUrl: './CreationStage.css'
})
export class CreationStageComponent implements OnInit, OnDestroy {
  private http = inject(HttpClient);

  // File upload properties
  selectedFile = signal<File | null>(null);
  isDragOver = false;
  isUploading = signal(false);
  uploadMessage = signal<{type: string, text: string, data?: any} | null>(null);
  
  // Extracted data properties
  extractedData = signal<{nom: string, prenom: string, cin: string, date_naissance: string} | null>(null);
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
  
  documentDragStates = signal<{[key: string]: boolean}>({
    convention: false,
    cv: false,
    assurance: false,
    lettre_motivation: false
  });
  
  // Candidate selection
  candidateMethod = signal<'new' | 'existing'>('new');
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
      this.selectedCandidate.set(null);
      this.extractedData.set(null);
      this.searchQuery.set('');
      this.filteredCandidates.set([]);
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
  }

  clearCandidateSelection(): void {
    this.selectedCandidate.set(null);
    this.searchQuery.set('');
    this.filteredCandidates.set([]);
    this.extractedData.set(null);
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
    const docs = this.documents();
    const stage = this.stageData();
    
    const hasCandidateData = !!(data?.nom && data?.prenom && data?.cin);
    
    const hasRequiredFiles = this.candidateMethod() === 'existing' ? 
      docs['cv'] : 
      (docs['cv'] && this.selectedFile());
    
    return !!(
      hasCandidateData &&
      hasRequiredFiles &&
      stage?.nature &&
      stage?.date_debut &&
      stage?.date_fin
    );
  }

  canCompleteStage(): boolean {
    const data = this.extractedData();
    const docs = this.documents();
    const stage = this.stageData();
    
    const hasCandidateData = !!(data?.nom && data?.prenom && data?.cin);
    
    const hasRequiredFiles = this.candidateMethod() === 'existing' ? 
      (docs['cv'] && docs['convention'] && docs['assurance']) :
      (docs['cv'] && docs['convention'] && docs['assurance'] && this.selectedFile());
    
    return !!(
      hasCandidateData &&
      hasRequiredFiles &&
      stage?.nature &&
      stage?.date_debut &&
      stage?.date_fin
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
      const docs = this.documents();
      const stage = this.stageData()!;
      const formData = new FormData();
      
      formData.append('nom', data.nom);
      formData.append('prenom', data.prenom);
      formData.append('cin', data.cin);
      formData.append('date_naissance', data.date_naissance);
      formData.append('status', 'stage_created');
      formData.append('candidate_method', this.candidateMethod());
      
      formData.append('nature', stage.nature);
      formData.append('date_debut', stage.date_debut);
      formData.append('date_fin', stage.date_fin);
      
      if (this.selectedSujet()) {
        formData.append('sujet_id', this.selectedSujet()!.id.toString());
      }
      
      if (this.candidateMethod() === 'new' && this.selectedFile()) {
        formData.append('cin_file', this.selectedFile()!);
      }

      if (docs['cv']) formData.append('cv_file', docs['cv']);
      if (docs['convention']) formData.append('convention_file', docs['convention']);
      if (docs['assurance']) formData.append('assurance_file', docs['assurance']);
      if (docs['lettre_motivation']) formData.append('lettre_motivation_file', docs['lettre_motivation']);

      const response = await this.http.post<any>(
        `${environment.apiUrl}resume/enregistrer_stagiaire/`,
        formData,
        { 
          headers: new HttpHeaders({
            'Authorization': `Bearer ${localStorage.getItem('access')}`
          })
        }
      ).toPromise();

      this.saveMessage.set({
        type: 'success',
        text: 'Stage créé avec succès! Vous pouvez maintenant ajouter les documents manquants (Convention et Assurance) pour compléter le dossier.'
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
      const docs = this.documents();
      const stage = this.stageData()!;
      const formData = new FormData();
      
      formData.append('nom', data.nom);
      formData.append('prenom', data.prenom);
      formData.append('cin', data.cin);
      formData.append('date_naissance', data.date_naissance);
      formData.append('status', 'dossier_complete');
      formData.append('candidate_method', this.candidateMethod());
      
      formData.append('nature', stage.nature);
      formData.append('date_debut', stage.date_debut);
      formData.append('date_fin', stage.date_fin);
      
      if (this.selectedSujet()) {
        formData.append('sujet_id', this.selectedSujet()!.id.toString());
      }
      
      if (this.candidateMethod() === 'new' && this.selectedFile()) {
        formData.append('cin_file', this.selectedFile()!);
      }

      if (docs['cv']) formData.append('cv_file', docs['cv']);
      if (docs['convention']) formData.append('convention_file', docs['convention']);
      if (docs['assurance']) formData.append('assurance_file', docs['assurance']);
      if (docs['lettre_motivation']) formData.append('lettre_motivation_file', docs['lettre_motivation']);

      const response = await this.http.post<any>(
        `${environment.apiUrl}resume/enregistrer_stagiaire/`,
        formData,
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
  onDocumentSelected(event: Event, documentType: string): void {
    const target = event.target as HTMLInputElement;
    const files = target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (this.isValidDocumentType(file)) {
        this.documents.update(docs => ({
          ...docs,
          [documentType]: file
        }));
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

  onDocumentDropped(event: DragEvent, documentType: string): void {
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
  }

  resetExtractedData(): void {
    this.extractedData.set(null);
    this.saveMessage.set(null);
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
    
    this.selectedFile.set(null);
    this.uploadMessage.set(null);
    this.extractedData.set(null);
    this.saveMessage.set(null);
    this.selectedCandidate.set(null);
    this.candidateMethod.set('new');
    this.searchQuery.set('');
    this.filteredCandidates.set([]);
    this.selectedSujet.set(null);
    this.sujetSearchQuery.set('');
    this.filteredSujets.set([]);
    
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
