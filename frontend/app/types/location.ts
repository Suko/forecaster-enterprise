/**
 * Location Types
 * Based on backend API reference
 */

export interface Location {
  id: string;
  client_id: string;
  location_id: string;
  name: string;
  address?: string | null;
  city?: string | null;
  country?: string | null;
  is_synced: boolean;
  created_at: string;
  updated_at: string;
}

export interface LocationCreate {
  location_id: string;
  name: string;
  address?: string | null;
  city?: string | null;
  country?: string | null;
}

export interface LocationUpdate {
  name?: string;
  address?: string | null;
  city?: string | null;
  country?: string | null;
}

export interface LocationListResponse {
  items: Location[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

