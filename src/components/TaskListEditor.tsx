// src/components/TaskListEditor.tsx

import React, { useState } from "react";
import { Trash2, PlusCircle } from "lucide-react";

// Assuming these types are correctly imported from src/types
import type { Profile, RoleData, SelectedKRA, MasterKRA } from '../types'; 

// This helper function will also be needed, so it can be defined here or imported if it was moved to a central helper file
const safeJsonParse = <T,>(s: string | undefined | null, fallback:T):T => { 
    if(!s) return fallback;
    try { return JSON.parse(s) as T; } catch { return fallback; }
};

export default function TaskListEditor({ tasks, onChange }: { tasks: string[]; onChange: (tasks: string[]) => void; }) {
  const add = () => onChange([...tasks, ""]);
  const del = (idx:number) => onChange(tasks.filter((_,i)=>i!==idx));
  const edit = (idx:number,val:string) => onChange(tasks.map((t,i)=>i===idx?val:t));
  
  return (
    <div className="space-y-3 mt-4">
      <h4 className="font-medium text-gray-700">Typical Day-to-Day Tasks</h4>
      {tasks.map((t,i)=>(
        <div key={i} className="flex items-center gap-2">
          <input value={t} onChange={e=>edit(i,e.target.value)} placeholder="e.g. Validate policy documents" className="flex-1 p-2 border rounded" />
          <button className="p-2 text-gray-500 hover:text-red-600" onClick={()=>del(i)} aria-label="Remove"><Trash2 size={16}/></button>
        </div>))}
      <button onClick={add} className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800"><PlusCircle size={16}/> Add Task</button>
    </div>
  );
}