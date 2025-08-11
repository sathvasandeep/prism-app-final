// src/pages/RegistrationPage.tsx

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const API_ROOT = (window as any).__PRISM_API__ ?? "http://127.0.0.1:8000";

export default function RegistrationPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setSuccess("");
        setIsLoading(true);

        if (!email || !password) {
            setError("Email and password are required.");
            setIsLoading(false);
            return;
        }

        try {
            const res = await fetch(`${API_ROOT}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || "Registration failed.");
            }

            setSuccess("Registration successful! Redirecting to login...");
            setTimeout(() => navigate('/login'), 2000);

        } catch (e) {
            setError((e as Error).message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
            <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
                <h1 className="text-2xl font-bold text-center text-gray-900">Create Your PRISM Account</h1>
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Email Address</label>
                        <input type="email" value={email} onChange={e => setEmail(e.target.value)} required
                               className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Password</label>
                        <input type="password" value={password} onChange={e => setPassword(e.target.value)} required
                               className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                    {error && <p className="text-sm text-red-600 text-center">{error}</p>}
                    {success && <p className="text-sm text-green-600 text-center">{success}</p>}
                    <div>
                        <button type="submit" disabled={isLoading}
                                className="w-full px-4 py-2 font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50">
                            {isLoading ? "Signing Up..." : "Sign Up"}
                        </button>
                    </div>
                </form>
                <p className="text-sm text-center text-gray-600">
                    Already have an account? <Link to="/login" className="font-medium text-blue-600 hover:underline">Log In</Link>
                </p>
            </div>
        </div>
    );
}