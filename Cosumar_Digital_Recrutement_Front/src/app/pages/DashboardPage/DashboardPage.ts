import { Component, EventEmitter, Output, HostListener, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { signal } from '@angular/core';

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [],
  templateUrl: './DashboardPage.html',
  styleUrl: './DashboardPage.css'
})
export class DashboardPage implements OnInit {
  // User information
  userName = signal('Ahmed Benali');
  userRole = signal('Responsable RH');
  userEmail = signal('ahmed.benali@cosumar.ma');
  
  // UI state
  activeMenuItem = signal('dashboard');
  isUserMenuOpen = signal(false);
  isSidebarCollapsed = signal(false);
  notificationCount = signal(5);
  isMobile = false;
  
  // Dashboard data (mock data for recruitment)
  totalPostes = signal('12');
  totalCandidatures = signal('186');
  entretiensEnCours = signal('24');
  totalUtilisateurs = signal('8');
  
  @Output() logoutRequest = new EventEmitter<void>();
  @Output() profileView = new EventEmitter<void>();
  @Output() profileEdit = new EventEmitter<void>();

  constructor(private router: Router) {}

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

  ngOnInit(): void {
    this.isMobile = window.innerWidth < 768;
  }
}