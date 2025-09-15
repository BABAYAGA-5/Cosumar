import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface StagiaireData {
  stageId: number;  // Add stage ID for navigation
  matricule: string;
  nom: string;
  prenom: string;
  statut: string;
  sujet?: string;
  nature: string;
  date_debut?: string;
  date_fin?: string;
  introduit_par?: {
    id: number;
    nom: string;
    prenom: string;
    email: string;
    departement: string;
  };
}

@Component({
  selector: 'StagiaireCard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './StagiaireCard.html',
  styleUrl: './StagiaireCard.css'
})
export class StagiaireCardComponent {
  @Input() stagiaire!: StagiaireData;

  getStatusColor(statut: string): string {
    const statusColors: { [key: string]: string } = {
      'annule': '#ef4444', // Red
      'en_attente_depot_dossier': '#f59e0b', // Orange
      'expire': '#dc2626', // Dark Red
      'en_attente_visite_medicale': '#3b82f6', // Blue
      'en_attente_des_signatures': '#8b5cf6', // Purple
      'stage_en_cours': '#10b981', // Green
      'en_attente_depot_rapport': '#06b6d4', // Cyan
      'en_attente_signature_du_rapport_par_l_encadrant': '#8b5cf6', // Purple
      'termine': '#22c55e' // Light Green
    };
    return statusColors[statut] || '#6b7280'; // Default gray
  }

  getStatusBgColor(statut: string): string {
    const statusBgColors: { [key: string]: string } = {
      'annule': '#fef2f2', // Light Red
      'en_attente_depot_dossier': '#fffbeb', // Light Orange
      'expire': '#fef2f2', // Light Red
      'en_attente_visite_medicale': '#eff6ff', // Light Blue
      'en_attente_des_signatures': '#f3f4f6', // Light Purple
      'stage_en_cours': '#f0fdf4', // Light Green
      'en_attente_depot_rapport': '#f0f9ff', // Light Cyan
      'en_attente_signature_du_rapport_par_l_encadrant': '#f3f4f6', // Light Purple
      'termine': '#f0fdf4' // Light Green
    };
    return statusBgColors[statut] || '#f9fafb'; // Default light gray
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

  getNatureColor(nature: string): string {
    const natureColors: { [key: string]: string } = {
      'stage': '#2E8B57', // Cosumar primary
      'pfe': '#228B22', // Cosumar secondary
      'alternance': '#32CD32' // Cosumar accent
    };
    return natureColors[nature] || '#6b7280';
  }

  getNatureText(nature: string): string {
    const natureTexts: { [key: string]: string } = {
      'stage': 'Stage',
      'pfe': 'PFE',
      'alternance': 'Alternance'
    };
    return natureTexts[nature] || nature;
  }

  getDepartmentText(departement: string): string {
    const departmentTexts: { [key: string]: string } = {
      'digital_factory': 'Digital Factory',
      'ressources_humaines': 'Ressources Humaines',
      'finance': 'Finance',
      'marketing': 'Marketing',
      'maintenance': 'Maintenance'
    };
    return departmentTexts[departement] || departement;
  }
}
