import React from "react";

import { Radar, RadarChart as ReRadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';

// Helper to convert skive data to recharts format
// Helper to convert skive data to recharts format, only for actually rated sub-competencies
const toRadarData = (data: Record<string, number>) =>
  Object.entries(data)
    .filter(([_, value]) => typeof value === 'number' && !isNaN(value))
    .map(([key, value]) => ({ subject: key, value }));

const RadarChart = ({ title, data }: { title: string; data: Record<string, number> }) => (
  <div style={{ width: 400, margin: 20 }}>
    <h3>{title}</h3>
    <ResponsiveContainer width="100%" height={300}>
      <ReRadarChart cx="50%" cy="50%" outerRadius="80%" data={toRadarData(data)}>
        <PolarGrid />
        <PolarAngleAxis dataKey="subject" />
        <PolarRadiusAxis angle={30} domain={[0, 10]} />
        <Radar name={title} dataKey="value" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
        <Tooltip />
      </ReRadarChart>
    </ResponsiveContainer>
  </div>
);

import { useEffect, useState } from "react";
import { generateArchetype } from "../../api/client";

interface Stage3Props {
  profileId: number;
  profession: number;
  department: number;
  role: number;
  skiveData: Record<string, Record<string, number>>;
  professionName?: string;
  departmentName?: string;
  roleName?: string;
}

const Stage3: React.FC<Stage3Props> = ({ profileId, profession, department, role, skiveData, professionName, departmentName, roleName }) => {
  const [radarData, setRadarData] = useState<any>(null);
  const [archetype, setArchetype] = useState<any>(null);
  const [professionInfo, setProfessionInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!profileId || !profession || !department || !role || !skiveData) return;
    setLoading(true);
    generateArchetype({
      profile_id: profileId,
      profession,
      department,
      role,
      skive: skiveData
    })
      .then(res => {
        setRadarData(res.radarData);
        setArchetype(res.archetype);
        setProfessionInfo(res.professionInfo);
        setLoading(false);
      })
      .catch(e => {
        setError(e.message || "Failed to load archetype");
        setLoading(false);
      });
  }, [profileId, profession, department, role, skiveData]);

  if (loading) return <div style={{ padding: 32 }}>Loading...</div>;
  if (error) return <div style={{ padding: 32, color: "red" }}>Error: {error}</div>;

  return (
    <div className="p-6 md:p-10 max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-blue-900">Stage 3: Archetypes</h1>
        <div className="flex flex-col md:flex-row gap-2 md:gap-6 mt-2 md:mt-0 text-sm md:text-base">
          <span className="bg-blue-50 text-blue-800 px-3 py-1 rounded font-medium">Profession: {professionName || professionInfo?.title || profession}</span>
          <span className="bg-green-50 text-green-800 px-3 py-1 rounded font-medium">Department: {departmentName || department}</span>
          <span className="bg-purple-50 text-purple-800 px-3 py-1 rounded font-medium">Role: {roleName || role}</span>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <section className="bg-white rounded-lg shadow p-6 border">
          <h2 className="text-xl font-semibold mb-2 text-gray-900">Overall SKIVE Radar</h2>
          <div className="flex flex-col items-center">
            <ResponsiveContainer width="100%" height={320} minWidth={300}>
              <ReRadarChart cx="50%" cy="50%" outerRadius="80%" data={toRadarData(skiveData.combined)}>
                <PolarGrid stroke="#e5e7eb" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 14, fill: '#374151' }} tickFormatter={(v: string) => v.length > 14 ? v.slice(0, 13) + '…' : v} />
                <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fontSize: 12, fill: '#9ca3af' }} />
                <Radar name="SKIVE" dataKey="value" stroke="#2563eb" fill="#3b82f6" fillOpacity={0.5} />
                <Tooltip />
              </ReRadarChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section className="bg-white rounded-lg shadow p-6 border">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">Archetype Details</h2>
          <h3 className="text-lg font-medium text-blue-800 mb-1">Archetype: {archetype?.name}</h3>
          <h4 className="text-md font-medium text-purple-700 mb-2">Global Archetype: {archetype?.globalName}</h4>
          <p className="text-gray-700 mb-2">{archetype?.narrative}</p>
          <div className="mt-4">
            <h4 className="font-semibold text-gray-800 mb-1">Profession Info</h4>
            <ul className="list-disc ml-5 text-gray-600 text-sm">
              <li><b>Years to Role:</b> {professionInfo?.yearsToRole}</li>
              <li><b>Qualifications:</b> {professionInfo?.qualifications?.join(", ")}</li>
              <li><b>Certifications:</b> {professionInfo?.certifications?.join(", ")}</li>
              <li><b>Salary Range:</b> {professionInfo?.salaryRange}</li>
              <li><b>Perks:</b> {professionInfo?.perks?.join(", ")}</li>
              <li><b>Highs:</b> {professionInfo?.highs}</li>
              <li><b>Lows:</b> {professionInfo?.lows}</li>
              <li><b>Career Pathway:</b> {professionInfo?.careerPathway}</li>
            </ul>
            {professionInfo?.videoUrl && (
              <div className="mt-4">
                <iframe
                  width="100%"
                  height="236"
                  src={professionInfo?.videoUrl}
                  title="Profession Video"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  className="rounded-lg shadow"
                ></iframe>
              </div>
            )}
          </div>
        </section>
      </div>
      <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-8">
        <section className="bg-white rounded-lg shadow p-6 border flex flex-col items-center">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">Skills</h3>
          <ResponsiveContainer width="100%" height={260} minWidth={260}>
            <ReRadarChart cx="50%" cy="50%" outerRadius="80%" data={toRadarData(skiveData.skills)}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: '#374151' }} />
              <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <Radar name="Skills" dataKey="value" stroke="#16a34a" fill="#4ade80" fillOpacity={0.5} />
              <Tooltip />
            </ReRadarChart>
          </ResponsiveContainer>
        </section>
        <section className="bg-white rounded-lg shadow p-6 border flex flex-col items-center">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">Knowledge</h3>
          <ResponsiveContainer width="100%" height={260} minWidth={260}>
            <ReRadarChart cx="50%" cy="50%" outerRadius="80%" data={toRadarData(skiveData.knowledge)}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: '#374151' }} />
              <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <Radar name="Knowledge" dataKey="value" stroke="#f59e42" fill="#fbbf24" fillOpacity={0.5} />
              <Tooltip />
            </ReRadarChart>
          </ResponsiveContainer>
        </section>
        <section className="bg-white rounded-lg shadow p-6 border flex flex-col items-center">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">Identity</h3>
          <ResponsiveContainer width="100%" height={260} minWidth={260}>
            <ReRadarChart cx="50%" cy="50%" outerRadius="80%" data={toRadarData(skiveData.identity)}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: '#374151' }} />
              <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <Radar name="Identity" dataKey="value" stroke="#7c3aed" fill="#a78bfa" fillOpacity={0.5} />
              <Tooltip />
            </ReRadarChart>
          </ResponsiveContainer>
        </section>
        <section className="bg-white rounded-lg shadow p-6 border flex flex-col items-center">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">Values</h3>
          <ResponsiveContainer width="100%" height={260} minWidth={260}>
            <ReRadarChart cx="50%" cy="50%" outerRadius="80%" data={toRadarData(skiveData.values)}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: '#374151' }} />
              <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <Radar name="Values" dataKey="value" stroke="#db2777" fill="#f472b6" fillOpacity={0.5} />
              <Tooltip />
            </ReRadarChart>
          </ResponsiveContainer>
        </section>
        <section className="bg-white rounded-lg shadow p-6 border flex flex-col items-center">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">Ethics</h3>
          <ResponsiveContainer width="100%" height={260} minWidth={260}>
            <ReRadarChart cx="50%" cy="50%" outerRadius="80%" data={toRadarData(skiveData.ethics)}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12, fill: '#374151' }} />
              <PolarRadiusAxis angle={30} domain={[0, 10]} tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <Radar name="Ethics" dataKey="value" stroke="#0ea5e9" fill="#38bdf8" fillOpacity={0.5} />
              <Tooltip />
            </ReRadarChart>
          </ResponsiveContainer>
        </section>
      </div>
    </div>
  );
};

export default Stage3;
