
// src/types/index.ts
export interface RoleData { profession:string; department: string; specificRole:string; description:string; key_responsibilities?: string; day_to_day_tasks?: string; }
export interface SelectedKRA { id: number | null; label: string; }
export interface MasterKRA { id: number; label: string; bucket: string; }
export interface SkiveRatings { skills:any; knowledge:any; identity:any; values:any; ethics:any; }
export interface AleDesign { learningObjectives:Record<string,string>; selectedAleComponents:Record<string,string[]>; selectedSkiveApproaches:Record<string,string[]>; }
export interface Profile { id:number|null; roleData:RoleData; skiveRatings:SkiveRatings; aleDesign:AleDesign; archetype:string|null; }
export interface SavedSummary { id:number; specific_role:string; profession:string; department: string; updated_at:string; archetype:string|null; }
export interface TaskPayload { id: number; competencyId: string; gcrId: string; uiComponentId: string; context: any; outputSchema: any; flavorId?: string; }

// A single rating data point for a radar chart
export interface RadarRating {
  name: string;
  value: number;
}

// The archetype narrative and competency breakdown
export interface Archetype {
  narrative: string;
  signature_competencies: string[];
  supporting_competencies: string[];
  foundational_expectations: string[];
}

// Data for a single radar chart (e.g., for one SKIVE category)
export interface RadarData {
  category: string;
  archetype: Archetype;
  ratings: RadarRating[];
}

// The consolidated radar chart data, averaging all categories
export interface ConsolidatedRadarData {
  archetype: Archetype;
  ratings: RadarRating[];
}

// The full payload from the multi-radar endpoint
export interface MultiRadarData {
  individual_radars: RadarData[];
  consolidated_radar: ConsolidatedRadarData;
}

export interface RoleSnapshot {
  day_in_the_life: string;
  highlights: string[];
  lowlights: string[];
  difficulty: string;
}

export interface Compensation {
  salary_range: string;
  perks: string[];
}

export interface Pathway {
  education: string[];
  certifications: string[];
  time_to_role: string;
}

export interface Testimonial {
  quote: string;
  author: string;
  video_url?: string;
}

export interface ProfileSummary {
  role_snapshot: RoleSnapshot;
  compensation: Compensation;
  pathway: Pathway;
  testimonials: Testimonial[];
  multi_radar_data?: MultiRadarData; // This will hold all the new radar and archetype data
}