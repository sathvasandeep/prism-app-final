// src/pages/SelectPathwayPage.tsx
import React from "react";
import { useNavigate } from "react-router-dom";

export default function SelectPathwayPage() {
  const navigate = useNavigate();

  const handlePathSelection = (path: string) => {
    if (path === "exploration") {
      navigate("/exploration-questions");
    } else if (path === "assessment") {
      navigate("/career-assessment");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-6">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <h1 className="text-2xl font-bold text-center mb-6">Choose Your Pathway</h1>

        <button
          onClick={() => handlePathSelection("exploration")}
          className="w-full mb-4 px-6 py-3 text-white bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold"
        >
          Career Exploration
        </button>

        <button
          onClick={() => handlePathSelection("assessment")}
          className="w-full px-6 py-3 text-white bg-green-600 hover:bg-green-700 rounded-lg font-semibold"
        >
          Career Assessment
        </button>
      </div>
    </div>
  );
}