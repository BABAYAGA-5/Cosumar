import { Component, EventEmitter, Output, HostListener, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { signal } from '@angular/core';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [],
  templateUrl: './DashboardPage.html',
  styleUrl: './DashboardPage.css'
})
export class DashboardPage implements OnInit {
  private http = inject(HttpClient);
  
  // User information
  userName = signal('Ahmed Benali');
  userRole = signal('Responsable RH');
  userEmail = signal('ahmed.benali@cosumar.ma');
  
  // UI state
  activeMenuItem = signal('dashboard');
  isUserMenuOpen = signal(false);
  isSidebarCollapsed = signal(true);
  notificationCount = signal(5);
  isMobile = false;
  
  // Dashboard data - now dynamic
  totalPostes = signal('--');
  totalCandidatures = signal('--');
  totalUtilisateurs = signal('--');
  pendingCandidatures = signal('--');
  
  // Loading state
  isLoading = signal(true);

  // File upload properties
  selectedFile = signal<File | null>(null);
  isDragOver = false;
  isUploading = signal(false);
  uploadMessage = signal<{type: string, text: string, data?: any} | null>(null);
  
  // Extracted data properties
  extractedData = signal<{nom: string, prenom: string, cin: string, date_naissance: string} | null>(null);
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
  
  @Output() logoutRequest = new EventEmitter<void>();
  @Output() profileView = new EventEmitter<void>();
  @Output() profileEdit = new EventEmitter<void>();

  constructor(private router: Router) {}

  ngOnInit(): void {
    this.isMobile = window.innerWidth < 768;
    this.loadDashboardStats();
  }

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access');
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }

  loadDashboardStats(): void {
    this.isLoading.set(true);
    
    this.http.get<any>(`${environment.apiUrl}dashboard/stats/`, {
      headers: this.getAuthHeaders()
    }).subscribe({
      next: (data) => {
        this.totalPostes.set(data.active_postes.toString());
        this.totalCandidatures.set(data.total_candidatures.toString());
        this.totalUtilisateurs.set(data.active_users.toString());
        this.pendingCandidatures.set(data.pending_candidatures.toString());
        this.isLoading.set(false);
      },
      error: (error) => {
        console.error('Error loading dashboard stats:', error);
        // Keep placeholder values on error
        this.totalPostes.set('N/A');
        this.totalCandidatures.set('N/A');
        this.totalUtilisateurs.set('N/A');
        this.pendingCandidatures.set('N/A');
        this.isLoading.set(false);
      }
    });
  }

  setActiveMenuItem(item: string): void {
    this.activeMenuItem.set(item);
    this.closeUserMenu();
  }

  toggleUserMenu(): void {
    this.isUserMenuOpen.update(value => !value);
  }

  closeUserMenu(): void {
    this.isUserMenuOpen.set(false);
  }

  toggleSidebar(): void {
    this.isSidebarCollapsed.update(value => !value);
    this.closeUserMenu();
    console.log('Sidebar collapsed:', this.isSidebarCollapsed); // Debug log
  }

  getPageTitle(): string {
    const titles: { [key: string]: string } = {
      'dashboard': 'Tableau de bord',
      'creation_stage': 'Création de Stage',
      'candidatures': 'Gestion des Candidatures',
      'candidats': 'Gestion des Candidats',
      'utilisateurs': 'Gestion des Utilisateurs',
      'domaines': 'Gestion des Domaines'
    };
    return titles[this.activeMenuItem()] || 'Tableau de bord';
  }

  viewProfile(): void {
    this.closeUserMenu();
    this.profileView.emit();
  }

  editProfile(): void {
    this.closeUserMenu();
    this.profileEdit.emit();
  }

  accountSettings(): void {
    this.closeUserMenu();
    // Navigate to account settings
    console.log('Navigate to account settings');
  }

  logout(): void {
    this.closeUserMenu();
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    this.router.navigate(['/login'], { replaceUrl: true });
  }

  // Close user menu when clicking outside
  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    const target = event.target as HTMLElement;
    if (!target.closest('.user-menu')) {
      this.closeUserMenu();
    }
  }

  @HostListener('window:resize', ['$event'])
  onResize(event: any): void {
    this.isMobile = event.target.innerWidth < 768;
    if (this.isMobile) {
      this.isSidebarCollapsed.set(false); // Reset collapse state on mobile
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
      // Automatically scan CIN when file is selected
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
        // Automatically scan CIN when file is dropped
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
    // Clean up the preview URL
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

  canSaveUser(): boolean {
    const data = this.extractedData();
    const docs = this.documents();
    // Check required fields and required documents
    return !!(
      data?.nom && 
      data?.prenom && 
      data?.cin && 
      docs['convention'] && 
      docs['cv'] && 
      docs['assurance']
    );
  }

  async saveUser(): Promise<void> {
    if (!this.canSaveUser()) {
      this.saveMessage.set({
        type: 'error',
        text: 'Veuillez remplir tous les champs requis et télécharger tous les documents obligatoires.'
      });
      return;
    }

    this.isSaving.set(true);
    this.saveMessage.set(null);

    try {
      const data = this.extractedData()!;
      const docs = this.documents();
      const formData = new FormData();
      
      // Add extracted data fields
      formData.append('nom', data.nom);
      formData.append('prenom', data.prenom);
      formData.append('cin', data.cin);
      formData.append('date_naissance', data.date_naissance);
      
      // Add the CIN file
      if (this.selectedFile()) {
        formData.append('cin_file', this.selectedFile()!);
      }

      // Add additional documents
      if (docs['convention']) {
        formData.append('convention', docs['convention']);
      }
      if (docs['cv']) {
        formData.append('cv', docs['cv']);
      }
      if (docs['assurance']) {
        formData.append('assurance', docs['assurance']);
      }
      if (docs['lettre_motivation']) {
        formData.append('lettre_motivation', docs['lettre_motivation']);
      }

      const response = await this.http.post<any>(
        `${environment.apiUrl}resume/enregistrer_utilisateur/`,
        formData,
        { 
          headers: new HttpHeaders({
            'Authorization': `Bearer ${localStorage.getItem('access')}`
          })
        }
      ).toPromise();

      this.saveMessage.set({
        type: 'success',
        text: 'Utilisateur enregistré avec succès!'
      });

      // Reset form after successful save
      setTimeout(() => {
        this.resetForm();
      }, 2000);

    } catch (error: any) {
      console.error('Error saving user:', error);
      this.saveMessage.set({
        type: 'error',
        text: error.error?.error || 'Erreur lors de l\'enregistrement de l\'utilisateur.'
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
    // Clean up the preview URL
    const currentUrl = this.cinPreviewUrl();
    if (currentUrl) {
      URL.revokeObjectURL(currentUrl);
      this.cinPreviewUrl.set(null);
    }
    
    this.selectedFile.set(null);
    this.uploadMessage.set(null);
    this.extractedData.set(null);
    this.saveMessage.set(null);
    
    // Reset documents
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