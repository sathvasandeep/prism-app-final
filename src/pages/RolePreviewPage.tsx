import React from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function RolePreviewPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const role = location.state?.role;

  if (!role) {
    return (
      <div className="p-8 text-center text-red-600 font-semibold">
        No role selected. Please go back and choose a career role to preview.
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      <button
        className="mb-4 text-blue-600 hover:underline"
        onClick={() => navigate(-1)}
      >
        ← Back to Role List
      </button>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-3xl font-bold mb-2 text-gray-900">
          {role.title || "Role Title"}
        </h1>
        <p className="text-gray-600 mb-4">
          {role.industry} / {role.department}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-800 mb-2">
              What does this role involve?
            </h2>
            <p className="text-gray-700 mb-4 whitespace-pre-line">
              {role.description || "Detailed role responsibilities and tasks."}
            </p>

            <h2 className="text-lg font-semibold text-gray-800 mb-2">
              Highs and Lows of the Role
            </h2>
            <ul className="list-disc ml-5 text-gray-700">
              {role.highs?.map((h, i) => (
                <li key={i}>{h}</li>
              )) || <li>Exciting career growth opportunities</li>}
              {role.lows?.map((l, i) => (
                <li key={i} className="text-red-500">{l}</li>
              )) || <li>May require weekend work or long hours</li>}
            </ul>
          </div>

          <div>
            <div className="aspect-video mb-4">
              {role.videoUrl ? (
                <iframe
                  width="100%"
                  height="100%"
                  src={role.videoUrl}
                  title="Role Preview Video"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  className="rounded-lg shadow"
                />
              ) : (
                <div className="bg-gray-200 rounded-lg h-full flex items-center justify-center text-gray-500">
                  No video available
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}