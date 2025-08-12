import type { FC } from 'react';
import { Sparkles } from 'lucide-react';
import type { ObjectiveLevels as ObjLevels, ObjectiveSource } from '../../api/client';
import { generateObjectives } from '../../api/client';

// Minimal copies of needed types from Stage1
interface SkiveSubCategory { [key: string]: number }
interface SkiveCategory { [key: string]: SkiveSubCategory | { [key: string]: number } }
interface SkiveRatings {
  skills: SkiveCategory;
  knowledge: SkiveCategory;
  identity: { [key: string]: number };
  values: { [key: string]: number };
  ethics: { [key: string]: number };
}

export interface ObjectiveLevels { basic: string; intermediate: string; advanced: string }
export type ObjectivesMap = Record<string, ObjectiveLevels & { source: ObjectiveSource }>; // key: path like skills.cognitive.analytical

interface Stage2Props {
  objectives: ObjectivesMap;
  setObjectives: (value: ObjectivesMap | ((prev: ObjectivesMap) => ObjectivesMap)) => void;
  skiveRatings: SkiveRatings;
  selectedProfession: string;
  selectedDept: string;
  selectedRole: string;
}

const Stage2: FC<Stage2Props> = ({ objectives, setObjectives, skiveRatings, selectedProfession, selectedDept, selectedRole }) => {
  const toTitle = (s: string) => s.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase());

  type Leaf = { path: string; label: string; group: string };
  const getLeaves = (): Leaf[] => {
    const leaves: Leaf[] = [];
    (['skills','knowledge'] as const).forEach(group => {
      const cat = skiveRatings[group] as SkiveCategory;
      Object.entries(cat).forEach(([sub, items]) => {
        if (typeof items === 'number') return;
        Object.keys(items as Record<string, number>).forEach((k) => {
          leaves.push({ path: `${group}.${sub}.${k}`, label: toTitle(k), group: toTitle(`${group}.${sub}`) });
        });
      });
    });
    (['identity','values','ethics'] as const).forEach(group => {
      const obj = skiveRatings[group] as Record<string, number>;
      Object.keys(obj).forEach(k => leaves.push({ path: `${group}.${k}`, label: toTitle(k), group: toTitle(group) }));
    });
    return leaves;
  };

  const roleKey = () => ({
    profession: selectedProfession ? parseInt(selectedProfession, 10) : null,
    department: selectedDept ? parseInt(selectedDept, 10) : null,
    role: selectedRole ? parseInt(selectedRole, 10) : null,
  });

  const generateForPath = async (path: string) => {
    try {
      const data = await generateObjectives(roleKey(), path);
      const levels = data.levels as ObjLevels;
      const source = (data.source as ObjectiveSource) || 'ai';
      setObjectives(prev => ({ ...prev, [path]: { ...levels, source } }));
    } catch (e) {
      console.error('Generate objectives error', e);
      alert('Failed to generate objectives.');
    }
  };

  const leaves = getLeaves();
  const grouped: Record<string, Leaf[]> = leaves.reduce((acc, leaf) => {
    acc[leaf.group] = acc[leaf.group] || [];
    acc[leaf.group].push(leaf);
    return acc;
  }, {} as Record<string, Leaf[]>);

  if (!selectedRole) {
    return <div>
      <h2 className="text-2xl font-bold mb-2">Stage 2: Simulation Objectives</h2>
      <p className="text-sm text-gray-600">Select a role in Stage 1 to enable objectives.</p>
    </div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-2">Stage 2: Simulation Objectives</h2>
      <p className="text-sm text-gray-600 mb-4">Translate SKIVE profile into SMART objectives across Basic, Intermediate, and Advanced levels. You can auto-generate with AI and edit as needed.</p>

      {Object.entries(grouped).map(([group, items]) => (
        <div key={group} className="mb-6">
          <h3 className="text-lg font-semibold mb-3">{group}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map(({ path, label }) => {
              const val = objectives[path] || { basic: '', intermediate: '', advanced: '', source: 'none' as ObjectiveSource };
              const setLevel = (level: keyof ObjectiveLevels, text: string) => setObjectives(prev => ({
                ...prev,
                [path]: { ...(prev[path] || { basic: '', intermediate: '', advanced: '', source: 'none' as ObjectiveSource }), [level]: text }
              }));
              return (
                <div key={path} className="border rounded-lg p-3 bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{label}</span>
                    <button onClick={() => generateForPath(path)} className="flex items-center gap-1 text-xs text-blue-600 hover:underline"><Sparkles size={14}/> Generate</button>
                  </div>
                  {val.source !== 'none' && (
                    <div className={`mb-2 inline-block px-2 py-0.5 rounded-full text-[10px] font-medium ${val.source==='ai' ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}`}>
                      {val.source==='ai' ? '🤖 AI Generated' : '📋 Default'}
                    </div>
                  )}
                  <label className="text-xs font-semibold">Basic</label>
                  <textarea value={val.basic} onChange={e => setLevel('basic', e.target.value)} className="w-full p-2 text-sm border rounded mb-2" rows={2} />
                  <label className="text-xs font-semibold">Intermediate</label>
                  <textarea value={val.intermediate} onChange={e => setLevel('intermediate', e.target.value)} className="w-full p-2 text-sm border rounded mb-2" rows={2} />
                  <label className="text-xs font-semibold">Advanced</label>
                  <textarea value={val.advanced} onChange={e => setLevel('advanced', e.target.value)} className="w-full p-2 text-sm border rounded" rows={2} />
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};

export default Stage2;
