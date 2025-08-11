// src/pages/UserProfileSelectionPage.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Briefcase } from 'lucide-react';

export default function UserProfileSelectionPage() {
  const navigate = useNavigate();

  const handleSelect = (role: 'student' | 'professional') => {
    localStorage.setItem('user_type', role);
    navigate('/select-pathway');
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 p-4">
      <div className="max-w-xl w-full bg-white p-8 rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-6 text-center text-gray-800">I am a...</h1>

        <div className="flex flex-col sm:flex-row gap-6">
          <button
            onClick={() => handleSelect('student')}
            className="flex items-center justify-center gap-4 p-6 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 w-full"
          >
            <User className="text-blue-600" size={32} />
            <span className="text-lg font-semibold text-blue-800">Student</span>
          </button>

          <button
            onClick={() => handleSelect('professional')}
            className="flex items-center justify-center gap-4 p-6 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 w-full"
          >
            <Briefcase className="text-green-600" size={32} />
            <span className="text-lg font-semibold text-green-800">Working Professional</span>
          </button>
        </div>
      </div>
    </div>
  );
}