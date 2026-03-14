export enum ProjectStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  ARCHIVED = 'archived',
}

export enum EntityStatus {
  SOLID_APPROVAL = 'solid_approval',
  LEANING_APPROVAL = 'leaning_approval',
  NEUTRAL = 'neutral',
  LEANING_DISAPPROVAL = 'leaning_disapproval',
  SOLID_DISAPPROVAL = 'solid_disapproval',
  UNKNOWN = 'unknown',
}

export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  GROUP_ADMIN = 'group_admin',
  EDITOR = 'editor',
}
export interface Jurisdiction {
  id: string;
  name: string;
  description?: string;
  level: string; // city, state, federal
  created_at: string;
}

export interface Entity {
  id: string;
  name: string;
  title?: string;
  entity_type: string;
  email?: string;
  phone?: string;
  website?: string;
  address?: string;
  district_name?: string;
  jurisdiction_id: string;
  image_url?: string;
}

export interface EntityStatusRecord {
  id: string;
  entity_id: string;
  project_id: string;
  status: EntityStatus;
  notes?: string;
  record_metadata?: Record<string, unknown>;
  updated_at: string;
  updated_by: string;
}

export interface StatusDistribution {
  solid_approval: number;
  leaning_approval: number;
  neutral: number;
  leaning_disapproval: number;
  solid_disapproval: number;
  unknown: number;
  total: number;
}

export interface MetricDisplayConfig {
  key: string;
  label: string;
  description?: string;
  format?: string;
  show_in_table?: boolean;
  show_in_tooltip?: boolean;
}

export interface DashboardConfig {
  representative_title?: string;
  status_labels?: Record<string, string>;
  metrics?: MetricDisplayConfig[];
}

export interface Project {
  id: string;
  title: string;
  description?: string;
  status: ProjectStatus;
  active: boolean;
  link?: string;
  preferred_status: EntityStatus;
  template_response?: string;
  jurisdiction_id: string;
  jurisdiction_name?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
  group_id: string;
  status_distribution?: StatusDistribution;
  slug?: string;
  dashboard_config?: DashboardConfig;
}

export interface ProjectCreateData {
  title: string;
  description?: string;
  status?: ProjectStatus;
  active?: boolean;
  link?: string;
  preferred_status?: EntityStatus;
  template_response?: string;
  jurisdiction_id?: string;
  group_id?: string;
}

export interface ProjectFilterParams {
  status?: ProjectStatus;
  group_id?: string;
  skip?: number;
  limit?: number;
  include_archived?: boolean;
}

export interface Group {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  projects?: Project[];
}

export interface AddressLookupRequest {
  address: string;
}

// Auth interfaces
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface UserRegisterData {
  email: string;
  name?: string;
  password: string;
  group_id: string;
  role?: string;
  is_active?: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name?: string;
  role: string;
  group_id: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
}

export interface PasswordChangeData {
  user_id: string;
  new_password: string;
}

export interface UserRoleChangeData {
  user_id: string;
  new_role: string;
}
