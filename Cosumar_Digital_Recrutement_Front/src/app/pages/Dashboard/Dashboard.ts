import { Component, signal, OnInit, inject, computed } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { Chart,ChartData,BarController, BarElement, DoughnutController, ArcElement, Tooltip, Legend, ChartOptions, LineController, LineElement, PointElement, LinearScale, CategoryScale, Title  } from 'chart.js';

Chart.register(DoughnutController,BarController, BarElement, ArcElement, Tooltip, Legend , LineController, LineElement, PointElement, LinearScale, CategoryScale, Title);
@Component({
  selector: 'Dashboard',
  standalone: true,
  imports: [BaseChartDirective,
    CommonModule
  ],
  templateUrl: './Dashboard.html',
  styleUrl: './Dashboard.css'
})
export class Dashboard implements OnInit {
  private http = inject(HttpClient);

  // Dashboard data - now dynamic
  nbSujets = signal('--');
  nbStagiaires = signal('--');
  nb_stage_en_cours = signal('--');
  nb_stage_en_attante_vm = signal('--');
  
  // nombre de stages en cours par
  nb_stage = signal(10);
  nb_alternance = signal(5);
  nb_pfe = signal(8);
  
  // Dynamic department data
  departementsStats = signal<any>({});
  availableDepartments = signal<{code: string, name: string}[]>([]);
  
  // Stages par département data
  stagesParDepartement = signal<any>({});
  availableStageStatuses = signal<{code: string, name: string}[]>([]);
  
  // Keep legacy signals for backward compatibility
  nb_stagiaires_dep_RH = signal(10);
  nb_stagiaires_dep_digital_factory = signal(5);
  nb_stagiaires_dep_logistique = signal(8);

  barType: 'bar' = 'bar';

barOptions: ChartOptions<'bar'> = {
  responsive: true,
  plugins: {
    legend: { 
      display: true,
      position: 'top'
    }
  },
  scales: {
    y: { beginAtZero: true }
  }
};

barData = computed<ChartData<'bar', number[], string>>(() => {
  const departments = this.availableDepartments();
  const departmentsStats = this.departementsStats();
  
  console.log('🔄 Computing barData...');
  console.log('🏢 Available departments:', departments);
  console.log('📊 Departments stats:', departmentsStats);
  
  if (departments.length === 0) {
    console.log('⚠️ No departments available, using fallback data');
    // Fallback to hardcoded data if no dynamic data available
    return {
      labels: ['RH', 'Digital Factory', 'Logistique'],
      datasets: [
        {
          label: 'Nombre de stagiaires',
          data: [
            this.nb_stagiaires_dep_RH(),
            this.nb_stagiaires_dep_digital_factory(),
            this.nb_stagiaires_dep_logistique()
          ],
          backgroundColor: ['#42A5F5', '#66BB6A', '#FFA726']
        }
      ]
    };
  }
  
  // Generate dynamic data from backend
  const labels = departments.map(dept => dept.name);
  const data = departments.map(dept => {
    const statKey = `nb_stagiaires_dep_${dept.code}`;
    const value = departmentsStats[statKey]?.count || 0;
    console.log(`📈 Department ${dept.name} (${dept.code}): looking for key "${statKey}", found value: ${value}`);
    return value;
  });
  
  console.log('📋 Final labels:', labels);
  console.log('📊 Final data:', data);
  
  // Generate colors dynamically based on number of departments
  const colors = this.generateColors(departments.length);
  
  const chartData = {
    labels: labels,
    datasets: [
      {
        label: 'Nombre de stagiaires',
        data: data,
        backgroundColor: colors
      }
    ]
  };
  
  console.log('📈 Final chart data:', chartData);
  return chartData;
});

// New chart for stages par département
departmentStagesBarType: 'bar' = 'bar';

departmentStagesBarOptions: ChartOptions<'bar'> = {
  responsive: true,
  plugins: {
    legend: { 
      display: true,
      position: 'top',
      onClick: (evt, legendItem, legend) => {
        // Custom legend click handler for filtering
        const index = legendItem.datasetIndex;
        const chart = legend.chart;
        const meta = chart.getDatasetMeta(index!);
        
        // Toggle dataset visibility
        meta.hidden = meta.hidden === null ? !chart.data.datasets[index!].hidden : !meta.hidden;
        chart.update();
      }
    },
    title: { 
      display: false
    },
    tooltip: {
      mode: 'index',
      intersect: false,
      callbacks: {
        title: (tooltipItems) => {
          return tooltipItems[0]?.label || '';
        },
        label: (context) => {
          const datasetLabel = context.dataset.label || '';
          const value = context.parsed.y;
          return `${datasetLabel}: ${value} stage${value > 1 ? 's' : ''}`;
        }
      }
    }
  },
  scales: {
    x: {
      stacked: false
    },
    y: { 
      beginAtZero: true,
      stacked: false
    }
  },
  interaction: {
    mode: 'index',
    intersect: false
  }
};

departmentStagesBarData = computed<ChartData<'bar', number[], string>>(() => {
  const departments = this.availableDepartments();
  const stagesData = this.stagesParDepartement();
  const availableStatuses = this.availableStageStatuses();
  
  console.log('🔄 Computing departmentStagesBarData...');
  console.log('🏢 Available departments:', departments);
  console.log('📊 Stages data:', stagesData);
  console.log('🏷️ Available statuses:', availableStatuses);
  
  if (Object.keys(stagesData).length === 0 || departments.length === 0) {
    console.log('⚠️ No stages data or departments available');
    return {
      labels: [],
      datasets: []
    };
  }
  
  const labels = departments.map(dept => dept.name);
  
  // Create a dataset for each status
  const datasets = availableStatuses.map((status, index) => {
    const data = departments.map(dept => {
      const deptData = stagesData[dept.code];
      if (deptData?.status_breakdown?.[status.code]) {
        return deptData.status_breakdown[status.code].count || 0;
      }
      return 0;
    });
    
    // Generate color for this status
    const colors = this.generateColors(availableStatuses.length);
    
    return {
      label: status.name,
      data: data,
      backgroundColor: colors[index],
      borderColor: colors[index],
      borderWidth: 1,
      hidden: false // All datasets visible by default
    };
  });
  
  console.log('📋 Final labels:', labels);
  console.log('📊 Final datasets:', datasets);
  
  const chartData = {
    labels: labels,
    datasets: datasets
  };
  
  console.log('📈 Final department stages chart data:', chartData);
  return chartData;
});

pieType: 'doughnut' = 'doughnut';

// Chart options
pieOptions: ChartOptions<'doughnut'> = {
  responsive: true,
  plugins: {
    legend: { position: 'bottom' }
  }
};

// Computed chart data
pieData = computed<ChartData<'doughnut', number[], string>>(() => ({
  labels: ['Stage', 'Alternance', 'PFE'],
  datasets: [
    { 
      data: [Number(this.nb_stage()), Number(this.nb_alternance()), Number(this.nb_pfe())],
      backgroundColor: ['#42A5F5', '#66BB6A', '#FFA726']
    }
  ]
}));
lineType: 'line' = 'line';

lineOptions: ChartOptions<'line'> = {
  responsive: true,
  plugins: { 
    legend: { display: true, position: 'bottom' }, 
    title: { display: true, text: 'Stagiaires terminés par année' }
  },
  scales: {
    y: { beginAtZero: true }
  }
};

lineData = computed<ChartData<'line', number[], string>>(() => ({
  labels: this.stagiairesTermineParAnnee().map(item => item.annee.toString()),
  datasets: [
    {
      label: 'Stagiaires terminés',
      data: this.stagiairesTermineParAnnee().map(item => item.nb_stagiaires_termine),
      borderColor: '#42A5F5',
      backgroundColor: '#90CAF9',
      fill: true,
      tension: 0.3
    }
  ]
}));
  // Loading state
  isLoading = signal(true);
  isMobile: boolean = false;

  // Ajout pour le diagramme en bâtons
  stagiairesTermineParAnnee = signal<{ annee: number, nb_stagiaires_termine: number }[]>([]);
  
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

    this.http.get<any>(`${environment.apiUrl}resume/stats_counts/`, {
      headers: this.getAuthHeaders()
    }).subscribe({
      next: (data) => {
        console.log('📊 Dashboard data received:', data);
        
        this.nbSujets.set(data.nb_sujets?.toString() ?? '--');
        this.nbStagiaires.set(data.nb_stagiaires?.toString() ?? '--');
        this.nb_stage_en_cours.set(data.nb_stage_en_cours?.toString() ?? '--');
        this.nb_stage_en_attante_vm.set(data.nb_stage_en_attante_vm?.toString() ?? '--');
        this.nb_stage.set(data.nb_stage ?? 0);
        this.nb_alternance.set(data.nb_alternance ?? 0);
        this.nb_pfe.set(data.nb_pfe ?? 0);
        
        // Update dynamic department data
        if (data.departements_stats) {
          console.log('🏢 Departments stats:', data.departements_stats);
          this.departementsStats.set(data.departements_stats);
        }
        if (data.available_departments) {
          console.log('📋 Available departments:', data.available_departments);
          this.availableDepartments.set(data.available_departments);
        }
        
        // Update stages par département data
        if (data.stages_par_departement) {
          console.log('📊 Stages par département:', data.stages_par_departement);
          this.stagesParDepartement.set(data.stages_par_departement);
        }
        if (data.available_stage_statuses) {
          console.log('🏷️ Available stage statuses:', data.available_stage_statuses);
          this.availableStageStatuses.set(data.available_stage_statuses);
        }
        
        // Keep legacy data for backward compatibility
        this.nb_stagiaires_dep_RH.set(data.nb_stagiaires_dep_finance ?? 0);
        this.nb_stagiaires_dep_digital_factory.set(data.nb_stagiaires_dep_digital_factory ?? 0);
        this.nb_stagiaires_dep_logistique.set(data.nb_stagiaires_dep_maintenance ?? 0);

        // Récupération des données pour le diagramme en bâtons
        this.stagiairesTermineParAnnee.set(data.stagiaires_termine_par_annee ?? []);
        this.isLoading.set(false);
        
        console.log('📈 Chart data after update:', this.barData());
      },
      error: (error) => {
        console.error('Error loading dashboard stats:', error);
        this.nbSujets.set('N/A');
        this.nbStagiaires.set('N/A');
        this.nb_stage_en_cours.set('N/A');
        this.nb_stage_en_attante_vm.set('N/A');
        this.isLoading.set(false);
      }
    });
  }

  // Generate dynamic colors for chart bars
  generateColors(count: number): string[] {
    const baseColors = [
      '#42A5F5', '#66BB6A', '#FFA726', '#EF5350', '#AB47BC', 
      '#26C6DA', '#FFCA28', '#5C6BC0', '#FF7043', '#9CCC65'
    ];
    
    if (count <= baseColors.length) {
      return baseColors.slice(0, count);
    }
    
    // Generate additional colors if needed
    const colors = [...baseColors];
    for (let i = baseColors.length; i < count; i++) {
      // Generate a color based on HSL with varying hue
      const hue = (i * 137.5) % 360; // Golden angle approximation for good distribution
      colors.push(`hsl(${hue}, 65%, 60%)`);
    }
    
    return colors;
  }

  // Get display name for stage status
  getStatusDisplayName(statusCode: string): string {
    const statuses = this.availableStageStatuses();
    const status = statuses.find(s => s.code === statusCode);
    return status?.name || statusCode;
  }

  // Helpers pour le diagramme
  getMaxBarValue() {
    const arr = this.stagiairesTermineParAnnee();
    return Math.max(...arr.map(item => item.nb_stagiaires_termine), 1);
  }
  stagiairesTermineParAnneeList() {
    return this.stagiairesTermineParAnnee();
  }

  // Helpers for template
  totalSujets() { return this.nbSujets(); }
  totalStagiaires() { return this.nbStagiaires(); }
  totalnb_stage_en_cours() { return this.nb_stage_en_cours(); }
  totalnb_stage_en_attante_vm() { return this.nb_stage_en_attante_vm(); }
  isLoadingStats() { return this.isLoading(); }
}