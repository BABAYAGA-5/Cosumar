import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';

@Component({
  selector: 'app-utilisateurs-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './UtilisateursList.html',
  styleUrls: ['./UtilisateursList.css']
})
export class UtilisateursList implements OnInit {
  utilisateurs: any[] = [];
  loading = true;
  error: string | null = null;
  
  // Filter properties
  searchTerm = '';
  selectedRole = '';
  selectedDepartment = '';
  selectedStatus = '';

  // Edit user modal properties
  editingUser: any = null;
  editForm: any = {};
  isSaving = false;
  
  // Available filter options
  roleOptions = [
    { value: '', label: 'Tous les rôles' },
    { value: 'admin', label: 'Administrateur' },
    { value: 'admin_rh', label: 'Admin RH' },
    { value: 'utilisateur_rh', label: 'Utilisateur RH' },
    { value: 'utilisateur', label: 'Utilisateur' }
  ];
  
  departmentOptions = [
    { value: '', label: 'Tous les départements' },
    { value: 'digital_factory', label: 'Digital Factory' },
    { value: 'ressources_humaines', label: 'Ressources Humaines' },
    { value: 'finance', label: 'Finance' },
    { value: 'marketing', label: 'Marketing' },
    { value: 'maintenance', label: 'Maintenance' }
  ];
  
  statusOptions = [
    { value: '', label: 'Tous les statuts' },
    { value: 'true', label: 'Actif' },
    { value: 'false', label: 'Inactif' }
  ];
  
  // Pagination properties
  currentPage = 1;
  pageSize = 25;
  totalCount = 0;
  totalPages = 0;
  hasNext = false;
  hasPrevious = false;
  nextPageNumber: number | null = null;
  previousPageNumber: number | null = null;
  
  private apiUrl = 'http://localhost:8000/auth/utilisateurs/';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.loadUtilisateurs();
  }

  loadUtilisateurs() {
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
    if (this.selectedRole) {
      url += `&role=${encodeURIComponent(this.selectedRole)}`;
    }
    if (this.selectedDepartment) {
      url += `&departement=${encodeURIComponent(this.selectedDepartment)}`;
    }
    if (this.selectedStatus) {
      url += `&is_active=${this.selectedStatus}`;
    }

    console.log('🔗 API URL with filters:', url); // Debug log

    this.http.get<any>(url, { headers }).subscribe({
      next: (response: any) => {
        console.log('📊 API Response:', response); // Debug log
        this.utilisateurs = response.results;
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
        console.error('❌ API Error:', err); // Debug log
        this.error = 'Erreur lors du chargement des utilisateurs';
        this.loading = false;
        console.error('Erreur:', err);
      }
    });
  }

  nextPage() {
    if (this.hasNext && this.nextPageNumber) {
      this.currentPage = this.nextPageNumber;
      this.loadUtilisateurs();
    }
  }

  previousPage() {
    if (this.hasPrevious && this.previousPageNumber) {
      this.currentPage = this.previousPageNumber;
      this.loadUtilisateurs();
    }
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.loadUtilisateurs();
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

  getRoleDisplayName(role: string): string {
    const roleMapping: { [key: string]: string } = {
      'admin': 'Administrateur',
      'admin_rh': 'Admin RH',
      'utilisateur_rh': 'Utilisateur RH',
      'utilisateur': 'Utilisateur'
    };
    
    return roleMapping[role] || role.toUpperCase();
  }

  getDepartementDisplayName(departement: string): string {
    const departementMapping: { [key: string]: string } = {
      'digital_factory': 'Digital Factory',
      'ressources_humaines': 'Ressources Humaines',
      'finance': 'Finance',
      'marketing': 'Marketing',
      'maintenance': 'Maintenance'
    };
    
    return departementMapping[departement] || departement || 'Non spécifié';
  }

  // Permission and role management methods
  isAdmin(): boolean {
    const userRole = localStorage.getItem('role');
    return userRole === 'admin';
  }

  canEditRole(user: any): boolean {
    // Admin can edit all roles except other admins
    return user.role !== 'admin';
  }

  getRoleOptionsForUser(user: any): { value: string, label: string }[] {
    // Admin can change roles but cannot demote other admins
    if (user.role === 'admin') {
      return [{ value: 'admin', label: 'Administrateur' }]; // Admin role is not editable
    }
    
    // For non-admin users, admin can assign any non-admin role
    return [
      { value: 'admin_rh', label: 'Admin RH' },
      { value: 'utilisateur_rh', label: 'Utilisateur RH' },
      { value: 'utilisateur', label: 'Utilisateur' }
    ];
  }

  updateUserRole(user: any, event: Event): void {
    const target = event.target as HTMLSelectElement;
    const newRole = target.value;
    
    if (newRole === user.role) {
      return; // No change
    }

    // Confirm the role change
    if (!confirm(`Êtes-vous sûr de vouloir changer le rôle de ${user.prenom} ${user.nom} vers "${this.getRoleDisplayName(newRole)}" ?`)) {
      // Reset the select to original value
      target.value = user.role;
      return;
    }

    // Call backend to update user role
    this.updateUserRoleInBackend(user.id, newRole, user);
  }

  private updateUserRoleInBackend(userId: number, newRole: string, user: any): void {
    const token = localStorage.getItem('access');
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });

    const body = { role: newRole };
    const url = `http://localhost:8000/auth/users/${userId}/update-role/`;

    // Add loading state to the select element
    const selectElement = document.querySelector(`select[data-user-id="${userId}"]`) as HTMLSelectElement;
    if (selectElement) {
      selectElement.disabled = true;
      selectElement.style.opacity = '0.7';
    }

    this.http.patch(url, body, { headers }).subscribe({
      next: (response: any) => {
        console.log('✅ Role updated successfully:', response);
        // Update the user in the local array
        user.role = newRole;
        // Show success message
        alert(`Rôle mis à jour avec succès vers "${this.getRoleDisplayName(newRole)}"`);
        
        // Remove loading state
        if (selectElement) {
          selectElement.disabled = false;
          selectElement.style.opacity = '1';
        }
      },
      error: (error: any) => {
        console.error('❌ Error updating role:', error);
        // Reset the select to original value
        if (selectElement) {
          selectElement.value = user.role;
          selectElement.disabled = false;
          selectElement.style.opacity = '1';
        }
        
        // Show error message based on server response
        const errorMessage = error.error?.error || 'Erreur lors de la mise à jour du rôle. Veuillez réessayer.';
        alert(errorMessage);
      }
    });
  }

  // Filter methods
  onSearchChange() {
    this.currentPage = 1; // Reset to first page when searching
    this.loadUtilisateurs();
  }

  onFilterChange() {
    this.currentPage = 1; // Reset to first page when filtering
    this.loadUtilisateurs();
  }

  clearFilters() {
    this.searchTerm = '';
    this.selectedRole = '';
    this.selectedDepartment = '';
    this.selectedStatus = '';
    this.currentPage = 1;
    this.loadUtilisateurs();
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

  // Edit user modal methods
  startEditing(user: any): void {
    console.log('🎯 Starting to edit user:', user);
    this.editingUser = { ...user }; // Create a copy
    this.editForm = {
      role: user.role,
      is_active: user.is_active
    };
    this.isSaving = false; // Explicitly set to false when starting edit
    console.log('📝 Edit form initialized:', this.editForm);
    console.log('👤 Editing user set:', this.editingUser);
    console.log('💾 isSaving set to:', this.isSaving);
  }

  cancelEditing(): void {
    this.editingUser = null;
    this.editForm = {};
    this.isSaving = false;
  }

  onRoleChange(event: any): void {
    console.log('🔄 Role changed to:', event.target.value);
    this.editForm.role = event.target.value;
    console.log('Updated editForm.role:', this.editForm.role);
  }

  onActiveChange(event: any): void {
    console.log('🔄 Active status changed to:', event.target.checked);
    this.editForm.is_active = event.target.checked;
    console.log('Updated editForm.is_active:', this.editForm.is_active);
  }

  saveUserChanges(): void {
    console.log('🔥 saveUserChanges called!');
    console.log('isSaving state:', this.isSaving);
    
    if (this.isSaving) {
      console.log('Already saving, returning early');
      return;
    }

    console.log('Setting isSaving to true');
    this.isSaving = true;
    
    const token = localStorage.getItem('access');
    console.log('Token:', token ? 'exists' : 'missing');
    
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });

    // Check what has changed and use appropriate endpoints
    const roleChanged = this.editForm.role !== this.editingUser.role;
    const activityChanged = this.editForm.is_active !== this.editingUser.is_active;

    console.log('🔍 Change detection:');
    console.log('Role changed:', roleChanged, `(${this.editForm.role} !== ${this.editingUser.role})`);
    console.log('Activity changed:', activityChanged, `(${this.editForm.is_active} !== ${this.editingUser.is_active})`);
    console.log('Current form:', this.editForm);
    console.log('Original user:', this.editingUser);
    console.log('Form role type:', typeof this.editForm.role, 'User role type:', typeof this.editingUser.role);
    console.log('Form active type:', typeof this.editForm.is_active, 'User active type:', typeof this.editingUser.is_active);

    // If nothing changed
    if (!roleChanged && !activityChanged) {
      console.log('No changes detected, stopping');
      this.isSaving = false;
      alert('Aucune modification détectée');
      return;
    }

    const updateObservables: any[] = [];

    // Update role if changed
    if (roleChanged) {
      const roleUrl = `http://localhost:8000/auth/users/${this.editingUser.id}/update-role/`;
      const roleData = { role: this.editForm.role };
      console.log('🚀 Adding role update:', roleData, 'to URL:', roleUrl);
      updateObservables.push(
        this.http.patch(roleUrl, roleData, { headers })
      );
    }

    // Update activity status if changed
    if (activityChanged) {
      const activityUrl = `http://localhost:8000/auth/users/${this.editingUser.id}/update-activity/`;
      const activityData = { is_active: this.editForm.is_active };
      console.log('🚀 Adding activity update:', activityData, 'to URL:', activityUrl);
      updateObservables.push(
        this.http.patch(activityUrl, activityData, { headers })
      );
    }

    console.log('📡 About to send', updateObservables.length, 'requests');

    if (updateObservables.length === 0) {
      console.log('❌ No requests to send! Stopping.');
      this.isSaving = false;
      alert('Aucune modification détectée');
      return;
    }

    // Execute all update requests using forkJoin
    forkJoin(updateObservables).subscribe({
      next: (responses) => {
        console.log('✅ User updated successfully:', responses);
        
        // Update the user in the local array
        const userIndex = this.utilisateurs.findIndex(u => u.id === this.editingUser.id);
        if (userIndex !== -1) {
          this.utilisateurs[userIndex] = { 
            ...this.utilisateurs[userIndex], 
            role: this.editForm.role,
            is_active: this.editForm.is_active
          };
        }
        
        // Show success message
        const changedFields = [];
        if (roleChanged) changedFields.push('rôle');
        if (activityChanged) changedFields.push('statut');
        
        alert(`${changedFields.join(' et ')} mis à jour avec succès`);
        this.isSaving = false; // Reset loading state before canceling
        this.cancelEditing();
      },
      error: (error) => {
        console.error('❌ Error updating user:', error);
        this.isSaving = false;
        
        // Show error message based on server response
        const errorMessage = error.error?.error || 'Erreur lors de la mise à jour de l\'utilisateur. Veuillez réessayer.';
        alert(errorMessage);
      }
    });
  }
}
