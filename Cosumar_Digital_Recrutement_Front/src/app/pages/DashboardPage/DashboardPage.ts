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
      'postes': 'Gestion des Postes',
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
}