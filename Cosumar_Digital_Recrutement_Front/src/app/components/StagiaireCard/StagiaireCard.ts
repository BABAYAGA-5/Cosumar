import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface StagiaireData {
  matricule: string;
  nom: string;
  prenom: string;
  statut: string;
  sujet?: string;
  nature: string;
  date_debut?: string;
  date_fin?: string;
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
      'en_attente_signature_de_l_encadrant': '#8b5cf6', // Purple
      'en_attente_signature_du_responsable_RH': '#8b5cf6', // Purple
      'en_attente_signature_du_stagiaire': '#8b5cf6', // Purple
      'stage_en_cours': '#10b981', // Green
      'en_attente_depot_rapport': '#06b6d4', // Cyan
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
      'en_attente_signature_de_l_encadrant': '#f3f4f6', // Light Purple
      'en_attente_signature_du_responsable_RH': '#f3f4f6', // Light Purple
      'en_attente_signature_du_stagiaire': '#f3f4f6', // Light Purple
      'stage_en_cours': '#f0fdf4', // Light Green
      'en_attente_depot_rapport': '#f0f9ff', // Light Cyan
      'termine': '#f0fdf4' // Light Green
    };
    return statusBgColors[statut] || '#f9fafb'; // Default light gray
  }

  getStatusText(statut: string): string {
    const statusTexts: { [key: string]: string } = {
      'annule': 'Annulé',
      'en_attente_depot_dossier': 'En attente de dépôt',
      'expire': 'Expiré',
      'en_attente_visite_medicale': 'Visite médicale',
      'en_attente_signature_de_l_encadrant': 'Signature encadrant',
      'en_attente_signature_du_responsable_RH': 'Signature RH',
      'en_attente_signature_du_stagiaire': 'Signature stagiaire',
      'stage_en_cours': 'En cours',
      'en_attente_depot_rapport': 'Dépôt rapport',
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
}
