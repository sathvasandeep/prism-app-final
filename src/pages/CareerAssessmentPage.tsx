import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function CareerAssessmentPage() {
  const navigate = useNavigate();

  const handleCodeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In future: Validate code with backend or redirect to payment
    alert("Assessment code submitted (stubbed)");
    navigate("/app"); // Or redirect to actual assessment when built
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-4 text-center text-gray-800">
          Career Assessment
        </h2>
        <p className="text-sm text-gray-600 mb-6 text-center">
          Enter your access code below to begin your personalized assessment. If you don’t have one, proceed to payment.
        </p>

        <form onSubmit={handleCodeSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Enter Access Code"
            className="w-full border border-gray-300 rounded px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 font-semibold"
          >
            Start Assessment
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            className="text-blue-500 hover:underline text-sm"
            onClick={() => alert("Redirecting to payment (stubbed)")}
          >
            Don’t have a code? Purchase access
          </button>
        </div>
      </div>
    </div>
  );
}