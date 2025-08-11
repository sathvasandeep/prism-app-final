// src/pages/LoginPage.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleLogin = () => {
    if (username === 'admin' && password === 'admin') {
        localStorage.setItem('userRole', 'admin');
        navigate('/dashboard');
    } else if (username === 'student' && password === 'student') {
        localStorage.setItem('userRole', 'student');
        navigate('/select-profile'); // 👈 new route for student
    } else {
        setError('Invalid username or password');
    }
    if (username === 'admin' && password === 'admin') {
    console.log("Logging in as admin...");
    localStorage.setItem('userRole', 'admin');
    navigate('/dashboard');
}
};

    const handleGoogleLoginSuccess = (credentialResponse: any) => {
    console.log("Google login success:", credentialResponse);
    // Assuming all Google users are students for now
    localStorage.setItem('userRole', 'student');
    navigate('/select-profile');
};

    const handleGoogleLoginError = () => {
        console.error("Google login failed");
        alert("Google login isn't available right now. Please use username/password.");
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
            <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
                <h1 className="text-2xl font-bold text-center text-gray-900">Login to PRISM</h1>

                <div>
                    <label className="block text-sm font-medium text-gray-700">Username</label>
                    <input
                        type="text"
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                        className="w-full px-4 py-2 mt-1 border rounded-md"
                        placeholder="Enter username"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700">Password</label>
                    <input
                        type="password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        className="w-full px-4 py-2 mt-1 border rounded-md"
                        placeholder="Enter password"
                    />
                </div>

                {error && <p className="text-sm text-red-500">{error}</p>}

                <button
                    onClick={handleLogin}
                    className="w-full px-4 py-2 font-semibold text-white bg-blue-600 rounded hover:bg-blue-700"
                >
                    Login
                </button>

                <div className="flex items-center justify-center">
                    <GoogleLogin
                        onSuccess={handleGoogleLoginSuccess}
                        onError={handleGoogleLoginError}
                    />
                </div>

                <p className="text-sm text-center text-gray-600">
                    Don't have an account?{' '}
                    <span className="font-medium text-blue-600">Sign Up (Coming soon)</span>
                </p>
            </div>
        </div>
    );
}