// src/components/KRASelector.tsx

import React, { useState, useEffect } from "react";
import { X } from "lucide-react";
import type { MasterKRA, SelectedKRA } from "../types";

const API_ROOT = (window as any).__PRISM_API__ ?? "http://127.0.0.1:8000";

// Fallback-safe JSON parse
const safeJsonParse = <T,>(s: string | undefined | null, fallback: T): T => {
  try {
    return s ? JSON.parse(s) : fallback;
  } catch {
    return fallback;
  }
};

export default function KRASelector({
  selected,
  onChange,
  profession,
  roleId,
}: {
  selected: SelectedKRA[];
  onChange: (k: SelectedKRA[]) => void;
  profession: string;
  roleId: number | null;
}) {
  const [master, setMaster] = useState<MasterKRA[]>([]);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    if (!roleId) {
      setMaster([]);
      return;
    }

    fetch(`${API_ROOT}/api/kras_master/${roleId}`)
      .then((r) => (r.ok ? r.json() : []))
      .then((data: MasterKRA[]) => setMaster(data))
      .catch(() => setMaster([]));
  }, [roleId]);

  const filtered = profession
    ? master.filter((m) => m.bucket === profession)
    : master;

  const toggle = (k: MasterKRA) => {
    const exists = selected.some((s) => s.id === k.id);
    exists
      ? onChange(selected.filter((s) => s.id !== k.id))
      : onChange([...selected, { id: k.id, label: k.label }]);
  };

  const addCustom = () => {
    if (!draft.trim()) return;
    if (
      selected.some(
        (s) => s.label.toLowerCase() === draft.trim().toLowerCase()
      )
    )
      return;
    onChange([...selected, { id: null, label: draft.trim() }]);
    setDraft("");
  };

  const remove = (idx: number) =>
    onChange(selected.filter((_, i) => i !== idx));

  return (
    <div className="space-y-3 mt-4">
      <h4 className="font-medium text-gray-700">Key Responsibilities & KRAs</h4>

      <div className="flex flex-wrap gap-2 p-2 border rounded bg-gray-50 min-h-[40px]">
        {selected.length === 0 && (
          <span className="text-sm text-gray-400">
            Select or add KRAs…
          </span>
        )}
        {selected.map((s, i) => (
          <span
            key={i}
            className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs"
          >
            {s.label}
            <button
              onClick={() => remove(i)}
              className="text-blue-600 hover:text-blue-900"
            >
              <X size={14} />
            </button>
          </span>
        ))}
      </div>

      <select
        onChange={(e) => {
          const id = parseInt(e.target.value);
          const k = filtered.find((m) => m.id === id);
          k && toggle(k);
          e.target.value = "";
        }}
        disabled={filtered.length === 0}
        className="w-full p-2 border rounded bg-white"
      >
        <option value="">-- Select from library --</option>
        {filtered.map((k) => (
          <option
            key={k.id}
            value={k.id}
            disabled={selected.some((s) => s.id === k.id)}
          >
            {k.label}
          </option>
        ))}
      </select>

      <div className="flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addCustom()}
          placeholder="Add custom KRA"
          className="flex-1 p-2 border rounded"
        />
        <button
          onClick={addCustom}
          className="px-3 py-2 bg-gray-200 rounded disabled:opacity-50"
          disabled={!draft.trim()}
        >
          Add
        </button>
      </div>
    </div>
  );
}