import { useEffect, useState } from 'react';
import type { FC } from 'react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import type { 
    ProfileSummary, 
    RadarData, 
    Archetype
} from '../types';

// --- LOCAL TYPE DEFINITIONS ---
type Stage = 'stage1' | 'stage2' | 'stage3';

// --- STAGE PROPS ---
interface Stage1Props { 
    // Define props for Stage1 if it were implemented
}

interface Stage2Props {
    // Define props for Stage2 if it were implemented
}

// --- REUSABLE CHILD COMPONENTS ---

const ArchetypeDisplay: FC<{ archetype: Archetype }> = ({ archetype }) => (
  <div className="space-y-3">
    <h4 className="font-bold text-lg">{archetype.narrative.split(':')[0]}</h4>
    <p className="text-sm text-gray-600 dark:text-gray-400">{archetype.narrative}</p>
    <div>
      <h5 className="font-semibold">Signature Competencies:</h5>
      <ul className="list-disc list-inside text-sm">
        {archetype.signature_competencies.map(c => <li key={c}>{c}</li>)}
      </ul>
    </div>
    <div>
      <h5 className="font-semibold">Supporting Competencies:</h5>
      <ul className="list-disc list-inside text-sm">
        {archetype.supporting_competencies.map(c => <li key={c}>{c}</li>)}
      </ul>
    </div>
  </div>
);

const MiniRadarChart: FC<{ data: RadarData }> = ({ data }) => (
  <ResponsiveContainer width="100%" height={300}>
    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data.ratings}>
      <PolarGrid />
      <PolarAngleAxis dataKey="name" />
      <PolarRadiusAxis angle={30} domain={[0, 10]} />
      <Radar name="Score" dataKey="value" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
    </RadarChart>
  </ResponsiveContainer>
);

const ConsolidatedRadarChart: FC<{ data: RadarData }> = ({ data }) => (
  <ResponsiveContainer width="100%" height={300}>
    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data.ratings}>
      <PolarGrid />
      <PolarAngleAxis dataKey="name" />
      <PolarRadiusAxis angle={30} domain={[0, 10]} />
      <Radar name="Score" dataKey="value" stroke="#82ca9d" fill="#82ca9d" fillOpacity={0.6} />
    </RadarChart>
  </ResponsiveContainer>
);

// --- STAGE COMPONENTS ---

const Stage1: FC<Stage1Props> = () => {
  return <div>Stage 1: Configuration (Not Implemented)</div>
}

const Stage2: FC<Stage2Props> = () => {
  return <div>Stage 2: Objectives (Not Implemented)</div>
}

const Stage3: FC<{ profileId: number | null }> = ({ profileId }) => {
  const [summary, setSummary] = useState<ProfileSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (profileId) {
      setIsLoading(true);
      setError(null);
      fetch(`/api/profile/multi-radar/${profileId}`)
        .then(res => {
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }
            return res.json();
        })
        .then((data: ProfileSummary) => {
          setSummary(data);
        })
        .catch(err => {
          console.error("Failed to fetch summary", err);
          setError(err.message);
        })
        .finally(() => {
            setIsLoading(false);
        });
    }
  }, [profileId]);

  if (isLoading) {
    return <div className="text-center p-8">Loading Profile Summary...</div>;
  }

  if (error) {
    return <div className="text-center p-8 text-red-500">Error loading summary: {error}</div>;
  }

  if (!summary) {
    return <div className="text-center p-8">No summary data available. Please complete previous stages or select a valid profile.</div>;
  }

  const consolidatedData = summary?.multi_radar_data?.consolidated_radar;
  const individualRadars = summary?.multi_radar_data?.individual_radars;

  return (
    <div className="space-y-6">
      {/* Consolidated View */}
      {consolidatedData && (
        <div className="border rounded p-4 dark:border-gray-700 dark:bg-gray-900">
          <h2 className="text-xl font-bold mb-4">Consolidated Profile</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ConsolidatedRadarChart data={consolidatedData as unknown as RadarData} />
            <ArchetypeDisplay archetype={consolidatedData.archetype} />
          </div>
        </div>
      )}

      {/* Per-Category View */}
      {individualRadars && (
        <div className="border rounded p-4 dark:border-gray-700 dark:bg-gray-900">
          <h2 className="text-xl font-bold mb-4">SKIVE Category Break-down</h2>
          <div className="space-y-8">
            {individualRadars.map((radarData) => (
              <div key={radarData.category} className="border-t pt-6 dark:border-gray-600">
                <h3 className="text-lg font-semibold capitalize mb-4">{radarData.category.replace(/_/g, ' ')}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <MiniRadarChart data={radarData} />
                  <ArchetypeDisplay archetype={radarData.archetype} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pathway & Compensation */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="border rounded p-4 space-y-2 dark:border-gray-700 dark:bg-gray-900">
          <div className="font-medium mb-1">Pathway</div>
          <div className="text-sm text-gray-700 dark:text-gray-300">Time to Role: {summary?.pathway?.time_to_role || '—'}</div>
          <div className="text-sm text-gray-700 dark:text-gray-300">Education: {summary?.pathway?.education?.join(', ') || '—'}</div>
        </div>
        <div className="border rounded p-4 space-y-3 dark:border-gray-700 dark:bg-gray-900">
          <div className="font-medium mb-1">Compensation</div>
          <div className="text-sm text-gray-700 dark:text-gray-300">
            <span className="font-medium">Salary Band:</span>
            <span className="ml-2 inline-block px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
              {summary?.compensation?.salary_range || '—'}
            </span>
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Perks</div>
            {(summary?.compensation?.perks?.length || 0) > 0 ? (
              <div className="flex flex-wrap gap-2">
                {summary!.compensation!.perks!.map((perk: string, i: number) => (
                  <span key={i} className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200">
                    {perk}
                  </span>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-700 dark:text-gray-300">—</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const PrismAdminApp = () => {
  const [stage, setStage] = useState<Stage>('stage3'); // Default to stage3 for testing
  const [profileId] = useState<number | null>(1); // Hardcode profileId for testing

  const renderContent = () => {
    switch (stage) {
      case 'stage1':
        return <Stage1 />;
      case 'stage2':
        return <Stage2 />;
      case 'stage3':
        return <Stage3 profileId={profileId} />;
      default:
        return <div>Welcome</div>;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Prism Admin</h1>
        <div className="flex border-b mb-6">
          <button onClick={() => setStage('stage1')} className={`px-4 py-2 ${stage === 'stage1' ? 'border-b-2 border-blue-500' : ''}`}>Stage 1: Config</button>
          <button onClick={() => setStage('stage2')} className={`px-4 py-2 ${stage === 'stage2' ? 'border-b-2 border-blue-500' : ''}`}>Stage 2: Objectives</button>
          <button onClick={() => setStage('stage3')} className={`px-4 py-2 ${stage === 'stage3' ? 'border-b-2 border-blue-500' : ''}`}>Stage 3: Summary</button>
        </div>
        {renderContent()}
      </div>
    </div>
  );
};

export default PrismAdminApp;