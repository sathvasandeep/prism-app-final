import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { PlusCircle, ServerCrash, RefreshCw } from "lucide-react";
import type { Profile, SavedSummary } from '../types/index.ts';
import { getInitialProfile } from '../utils.ts';

const API_ROOT = (window as any).__PRISM_API__ ?? "http://127.0.0.1:8000";

export default function DashboardPage() {
    const [list, setList] = useState<SavedSummary[]>([]);
    const [state, setState] = useState<{ loading: boolean; err: string | null }>({ loading: true, err: null });
    const navigate = useNavigate();

    const userRole = localStorage.getItem('userRole');

    useEffect(() => {
        if (!userRole) {
            navigate('/login');
        } else {
            loadAll();
        }
    }, []);

    const loadAll = async () => {
        setState({ loading: true, err: null });
        try {
            const res = await fetch(`${API_ROOT}/api/simulations`);
            if (!res.ok) throw new Error(`Server connection failed with status ${res.status}`);
            const data = await res.json();
            setList(data);
        } catch (e) {
            setState({ loading: false, err: (e as Error).message });
        } finally {
            setState(s => ({ ...s, loading: false }));
        }
    };

    const loadOne = async (id: number) => {
        setState({ loading: true, err: null });
        try {
            const res = await fetch(`${API_ROOT}/api/simulations/${id}`);
            if (!res.ok) throw new Error(`Failed to load profile: ${res.status}`);
            const loadedData = await res.json();
            const completeProfile = { ...getInitialProfile(), ...loadedData, id: loadedData.id };
            navigate('/app', { state: { activeProfile: completeProfile } });
        } catch (e) {
            setState({ loading: false, err: (e as Error).message });
        }
    };

    const handleCreateNew = () => {
        navigate('/app', { state: { activeProfile: getInitialProfile() } });
    };

    const handleLogout = () => {
        localStorage.removeItem('userRole');
        navigate('/login');
    };

    return (
        <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
            <div className="bg-white rounded-lg shadow-lg">
                <header className="p-6 border-b flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">PRISM Profile Dashboard</h1>
                        <p className="text-gray-600">Logged in as: <strong>{userRole}</strong></p>
                    </div>
                    <button onClick={handleLogout} className="text-sm text-red-500 hover:text-red-700 underline">Logout</button>
                </header>

                <main className="p-6">
                    <button onClick={handleCreateNew} className="w-full flex items-center justify-center gap-2 mb-6 px-4 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700">
                        <PlusCircle size={20} /> Create New Profile
                    </button>

                    <h2 className="text-lg font-semibold text-gray-800 mb-4">Existing Profiles</h2>

                    {state.loading && <p className="text-center py-4">Loading profiles…</p>}

                    {state.err && (
                        <div className="py-8 px-4 text-center bg-red-50 border-red-200 rounded-lg">
                            <ServerCrash className="mx-auto text-red-500 mb-2" size={32} />
                            <p className="font-semibold text-red-700">Connection Error</p>
                            <p className="text-sm text-red-600 mb-4">{state.err}</p>
                            <button onClick={loadAll} className="flex items-center mx-auto gap-2 px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200">
                                <RefreshCw size={14} /> Retry
                            </button>
                        </div>
                    )}

                    {(!state.loading && !state.err) && (list.length === 0 ? (
                        <p className="text-center text-gray-500 py-4">No saved profiles found.</p>
                    ) : (
                        <ul className="space-y-3">
                            {list.map(p => (
                                <li key={p.id} onClick={() => loadOne(p.id)} className="grid grid-cols-3 items-center p-4 bg-gray-50 border rounded-lg hover:bg-blue-50 hover:border-blue-300 cursor-pointer">
                                    <div className="col-span-2">
                                        <p className="font-semibold text-blue-800">{p.specific_role || "Untitled Role"}</p>
                                        <p className="text-sm text-gray-600">{p.profession}{p.department ? ` / ${p.department}` : ''}</p>
                                        {p.archetype && <span className="inline-block mt-1 text-xs font-medium bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">{p.archetype}</span>}
                                    </div>
                                    <div className="text-right text-sm">
                                        <p className="text-gray-500">Last updated</p>
                                        <p className="font-medium text-gray-700">{p.updated_at ? new Date(p.updated_at).toLocaleDateString() : 'N/A'}</p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    ))}
                </main>
            </div>
        </div>
    );
}