import { useQuery } from '@tanstack/react-query';
import type { QueryKey } from '@tanstack/react-query';

export interface SelectOption { id: number; name: string }

async function jsonFetch<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export const getProfessions = () => jsonFetch<SelectOption[]>('/api/professions');
export const getDepartments = (professionId: string) => jsonFetch<SelectOption[]>(`/api/departments?profession_id=${professionId}`);
export const getRoles = (departmentId: string) => jsonFetch<SelectOption[]>(`/api/roles?department_id=${departmentId}`);

export const useProfessions = () =>
  useQuery({ queryKey: ['professions'] as QueryKey, queryFn: getProfessions, staleTime: 5 * 60 * 1000, retry: 2 });

export const useDepartments = (professionId?: string) =>
  useQuery({ queryKey: ['departments', professionId] as QueryKey, queryFn: () => getDepartments(professionId!), enabled: !!professionId, staleTime: 5 * 60 * 1000, retry: 2 });

export const useRoles = (departmentId?: string) =>
  useQuery({ queryKey: ['roles', departmentId] as QueryKey, queryFn: () => getRoles(departmentId!), enabled: !!departmentId, staleTime: 5 * 60 * 1000, retry: 2 });

export interface ObjectiveLevels { basic: string; intermediate: string; advanced: string }
export type ObjectiveSource = 'none' | 'ai' | 'default';

export async function generateObjectives(key: { profession: number|null; department: number|null; role: number|null }, path: string) {
  const res = await fetch('/api/ai/objectives', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key, path }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<{ levels: ObjectiveLevels; source: ObjectiveSource }>;
}

export async function generateArchetype(payload: {
  profile_id: number;
  profession: number;
  department: number;
  role: number;
  skive: Record<string, Record<string, number>>;
}) {
  const res = await fetch('/api/archetype', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<{
    radarData: Record<string, Record<string, number>>;
    archetype: { name: string; narrative: string; globalName: string };
    professionInfo: any;
  }>;
}

