// src/pages/PrismApp.tsx

import React, { useEffect, useState, FC, MouseEvent, KeyboardEvent, ChangeEvent } from 'react';
import { Save, Sparkles, ListChecks, ClipboardList, ChevronDown } from 'lucide-react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';

// --- TYPE DEFINITIONS ---
type Stage = 'stage1' | 'stage2' | 'stage3';

interface SelectOption {
  id: number;
  name: string;
}

interface SkiveSubCategory {
  [key: string]: number;
}

interface SkiveCategory {
  [key: string]: SkiveSubCategory | { [key: string]: number };
}

interface SkiveRatings {
  skills: SkiveCategory;
  knowledge: SkiveCategory;
  identity: { [key: string]: number };
  values: { [key: string]: number };
  ethics: { [key: string]: number };
}

interface AccordionItemProps {
  label: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

interface RangeWithTicksProps {
  value: number;
  onChange: (v: number) => void;
}

interface EditableListProps {
  items: string[];
  onChange: (items: string[]) => void;
  title: string;
  icon: React.ReactNode;
}

interface Stage1Props {
  professions: SelectOption[];
  departments: SelectOption[];
  roles: SelectOption[];
  selectedProfession: string;
  setSelectedProfession: React.Dispatch<React.SetStateAction<string>>;
  selectedDept: string;
  setSelectedDept: React.Dispatch<React.SetStateAction<string>>;
  selectedRole: string;
  setSelectedRole: React.Dispatch<React.SetStateAction<string>>;
  profileName: string;
  setProfileName: React.Dispatch<React.SetStateAction<string>>;
  dayToDay: string[];
  setDayToDay: React.Dispatch<React.SetStateAction<string[]>>;
  kras: string[];
  setKras: React.Dispatch<React.SetStateAction<string[]>>;
  skiveRatings: SkiveRatings;
  setSkiveRatings: React.Dispatch<React.SetStateAction<SkiveRatings>>;
  competencyDescriptions: Record<string, string>;
  handleSaveConfig: () => Promise<void>;
  generateDayToDay: () => Promise<void>;
  generateKras: () => Promise<void>;
}

// --- REUSABLE CHILD COMPONENTS ---

const AccordionItem: FC<AccordionItemProps> = ({ label, children, defaultOpen = true }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const handleToggle = () => {
    setIsOpen(prev => !prev);
  };

  return (
    <div className="border rounded-md overflow-hidden">
      <div
        role="button"
        tabIndex={0}
        onClick={handleToggle}
        onKeyDown={(e: KeyboardEvent) => (e.key === 'Enter' || e.key === ' ') && handleToggle()}
        className="flex justify-between items-center p-3 bg-gray-100 dark:bg-gray-700 cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600"
      >
        <h3 className="font-semibold text-gray-800 dark:text-gray-200 pointer-events-none">{label}</h3>
        <ChevronDown
          className={`transform transition-transform duration-200 pointer-events-none ${isOpen ? 'rotate-180' : ''}`}
          size={20}
        />
      </div>
      {isOpen && (
        <div onClick={(e: MouseEvent) => e.stopPropagation()} onMouseDown={(e: MouseEvent) => e.stopPropagation()}>
          {children}
        </div>
      )}
    </div>
  );
};

const RangeWithTicks: FC<RangeWithTicksProps> = ({ value, onChange }) => {
  return (
    <div className="flex flex-col items-center w-full">
      <input
        type="range"
        min="1"
        max="10"
        value={value}
        onChange={(e: ChangeEvent<HTMLInputElement>) => onChange(parseInt(e.target.value, 10))}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
      />
      <div className="w-full flex justify-between text-xs px-1 mt-1 text-gray-500 dark:text-gray-400">
        {[...Array(10)].map((_, i) => <span key={i}>{i + 1}</span>)}
      </div>
    </div>
  );
};

const EditableList: FC<EditableListProps> = ({ items, onChange, title, icon }) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editText, setEditText] = useState('');

  const handleEdit = (index: number) => {
    setEditingIndex(index);
    setEditText(items[index]);
  };

  const handleSave = (index: number) => {
    if (editText.trim() === '') return handleRemove(index);
    const newItems = [...items];
    newItems[index] = editText;
    onChange(newItems);
    setEditingIndex(null);
  };

  const handleAdd = () => {
    const newItems = [...items, 'New item'];
    onChange(newItems);
    setEditingIndex(newItems.length - 1);
    setEditText('New item');
  };

  const handleRemove = (index: number) => {
    onChange(items.filter((_, i) => i !== index));
  };

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
      <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">{icon} {title}</h3>
      <ul className="space-y-2">
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            {editingIndex === index ? (
              <input
                type="text"
                value={editText}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setEditText(e.target.value)}
                onBlur={() => handleSave(index)}
                onKeyDown={(e: KeyboardEvent) => e.key === 'Enter' && handleSave(index)}
                className="flex-grow p-1 border rounded bg-gray-50 dark:bg-gray-700"
                autoFocus
              />
            ) : (
              <span className="flex-grow">{item}</span>
            )}
            <button onClick={() => (editingIndex === index ? handleSave(index) : handleEdit(index))} className="text-blue-500 text-sm">{editingIndex === index ? 'Save' : 'Edit'}</button>
            <button onClick={() => handleRemove(index)} className="text-red-500 text-sm">Remove</button>
          </li>
        ))}
      </ul>
      <button onClick={handleAdd} className="mt-3 text-blue-600">+ Add Item</button>
    </div>
  );
};

const StagePlaceholder: FC<{ title: string }> = ({ title }) => (
  <div className="p-6">
    <h2 className="text-xl font-semibold">{title}</h2>
    <p className="text-gray-600 dark:text-gray-400 mt-2">Coming soon.</p>
  </div>
);

const Stage1: FC<Stage1Props> = ({
  professions, departments, roles,
  selectedProfession, setSelectedProfession,
  selectedDept, setSelectedDept,
  selectedRole, setSelectedRole,
  profileName, setProfileName,
  dayToDay, setDayToDay,
  kras, setKras,
  skiveRatings, setSkiveRatings,
  competencyDescriptions,
  handleSaveConfig, generateDayToDay, generateKras
}) => {

  const handleSkiveChange = (mainCategory: keyof SkiveRatings, subCategory: string, item: string, value: number) => {
    setSkiveRatings(prev => {
      const newRatings = JSON.parse(JSON.stringify(prev));
      newRatings[mainCategory][subCategory][item] = value;
      return newRatings;
    });
  };

  const handleSimpleSkiveChange = (mainCategory: keyof SkiveRatings, item: string, value: number) => {
    setSkiveRatings(prev => {
      const newRatings = JSON.parse(JSON.stringify(prev));
      newRatings[mainCategory][item] = value;
      return newRatings;
    });
  };

  const radarData = () => {
    const avg = (vals: number[]) => (vals.length > 0 ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0);

    const skillsVals = Object.values(skiveRatings.skills).flatMap(sub => Object.values(sub).flatMap(item => Object.values(item as SkiveSubCategory)));
    const knowledgeVals = Object.values(skiveRatings.knowledge).flatMap(sub => Object.values(sub).flatMap(item => Object.values(item as SkiveSubCategory)));
    const identityVals = Object.values(skiveRatings.identity);
    const valuesVals = Object.values(skiveRatings.values);
    const ethicsVals = Object.values(skiveRatings.ethics);

    return [
      { subject: 'Skills', A: avg(skillsVals as number[]) },
      { subject: 'Knowledge', A: avg(knowledgeVals as number[]) },
      { subject: 'Identity', A: avg(identityVals as number[]) },
      { subject: 'Values', A: avg(valuesVals as number[]) },
      { subject: 'Ethics', A: avg(ethicsVals as number[]) },
    ];
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Stage 1: Role Epistemic Frame / Profiler</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 p-4 border rounded-lg bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Profession</label>
          <select value={selectedProfession} onChange={(e) => setSelectedProfession(e.target.value)} className="w-full p-2 border rounded bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600">
            <option value="">Select Profession</option>
            {professions.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Department</label>
          <select value={selectedDept} onChange={(e) => setSelectedDept(e.target.value)} className="w-full p-2 border rounded bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600" disabled={!selectedProfession}>
            <option value="">Select Department</option>
            {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
          <select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value)} className="w-full p-2 border rounded bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600" disabled={!selectedDept}>
            <option value="">Select Role</option>
            {roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
          </select>
        </div>
      </div>

      {selectedRole && (
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Profile Name</label>
            <input
              type="text"
              value={profileName}
              onChange={(e) => setProfileName(e.target.value)}
              placeholder="Enter a name for this role profile..."
              className="w-full p-2 border rounded bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <button onClick={generateDayToDay} className="flex items-center gap-2 text-sm text-blue-600 hover:underline"><Sparkles size={14} /> Generate Day-to-Day Activities</button>
              <EditableList items={dayToDay} onChange={setDayToDay} title="Day-to-Day Activities" icon={<ListChecks size={20} />} />
            </div>
            <div className="space-y-2">
              <button onClick={generateKras} className="flex items-center gap-2 text-sm text-blue-600 hover:underline"><Sparkles size={14} /> Generate KRAs</button>
              <EditableList items={kras} onChange={setKras} title="Key Responsibility Areas (KRAs)" icon={<ClipboardList size={20} />} />
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-xl mb-3">SKIVE Profile</h3>
            <div className="space-y-2">
              {Object.entries(skiveRatings).map(([mainCategory, subCategories]) => (
                <AccordionItem key={mainCategory} label={mainCategory.charAt(0).toUpperCase() + mainCategory.slice(1)}>
                  <div className="p-4 space-y-2 bg-gray-50 dark:bg-gray-900">
                    {Object.entries(subCategories).map(([subCategory, items]) => {
                      const isSimple = typeof Object.values(items)[0] !== 'object';
                      if (isSimple) {
                        return (
                          <div key={subCategory} className="p-4 bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700">
                            <p className="mb-2 text-sm text-gray-600 dark:text-gray-400">{competencyDescriptions[subCategory] || 'No description available.'}</p>
                            <RangeWithTicks value={items as unknown as number} onChange={(newValue) => handleSimpleSkiveChange(mainCategory as keyof SkiveRatings, subCategory, newValue)} />
                          </div>
                        );
                      }
                      return (
                        <AccordionItem key={subCategory} label={subCategory.charAt(0).toUpperCase() + subCategory.slice(1)} defaultOpen={false}>
                          <div className="p-4 space-y-3 bg-gray-100 dark:bg-gray-800">
                            {Object.entries(items).map(([item, value]) => (
                              <div key={item}>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">{item.replace(/([A-Z])/g, ' $1')}</label>
                                <p className="mb-2 text-xs text-gray-500 dark:text-gray-400">{competencyDescriptions[item] || 'No description available.'}</p>
                                <RangeWithTicks value={value as number} onChange={(newValue) => handleSkiveChange(mainCategory as keyof SkiveRatings, subCategory, item, newValue)} />
                              </div>
                            ))}
                          </div>
                        </AccordionItem>
                      );
                    })}
                  </div>
                </AccordionItem>
              ))}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 flex justify-center">
            <RadarChart cx={300} cy={150} outerRadius={100} width={600} height={300} data={radarData()}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" />
              <PolarRadiusAxis angle={30} domain={[0, 10]} />
              <Radar name="SKIVE" dataKey="A" stroke="#2563eb" fill="#2563eb" fillOpacity={0.4} />
            </RadarChart>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- MAIN APP COMPONENT ---

const PrismAdminApp: FC = () => {
  const [stage, setStage] = useState<Stage>('stage1');
  const [professions, setProfessions] = useState<SelectOption[]>([]);
  const [departments, setDepartments] = useState<SelectOption[]>([]);
  const [roles, setRoles] = useState<SelectOption[]>([]);
  const [selectedProfession, setSelectedProfession] = useState<string>('');
  const [selectedDept, setSelectedDept] = useState<string>('');
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [profileName, setProfileName] = useState<string>('');
  const [dayToDay, setDayToDay] = useState<string[]>([]);
  const [kras, setKras] = useState<string[]>([]);
  const [skiveRatings, setSkiveRatings] = useState<SkiveRatings>({
    skills: {
      cognitive: { analytical: 1, decisionMaking: 1, strategicPlanning: 1, criticalEvaluation: 1 },
      interpersonal: { communication: 1, collaboration: 1, empathy: 1, negotiation: 1 },
      psychomotor: { precision: 1, proceduralExecution: 1, coordination: 1 },
      metacognitive: { reflection: 1, adaptability: 1, selfRegulation: 1 },
    },
    knowledge: {
      declarative: { conceptual: 1, factual: 1, theoretical: 1 },
      procedural: { methods: 1, processes: 1, techniques: 1 },
      conditional: { whenToApply: 1, contextualUse: 1 },
    },
    identity: { professionalRole: 1, communityBelonging: 1, selfEfficacy: 1, dispositions: 1 },
    values: { coreValues: 1, epistemicValues: 1, stakeholderValues: 1 },
    ethics: { deontological: 1, consequentialist: 1, virtue: 1 },
  });

  const competencyDescriptions: Record<string, string> = {
    analytical: "Ability to break down complex problems and identify patterns",
    decisionMaking: "Capacity to make informed choices under uncertainty",
    strategicPlanning: "Long-term thinking and planning capabilities",
    criticalEvaluation: "Assessing the validity and relevance of information",
    communication: "Effective verbal and written communication",
    collaboration: "Working effectively with others toward common goals",
    empathy: "Understanding and sharing the feelings of others",
    negotiation: "Reaching agreements through discussion and compromise",
    precision: "Executing tasks with exactness and accuracy",
    proceduralExecution: "Following established procedures consistently",
    coordination: "Synchronizing movements or actions effectively",
    reflection: "Thinking about one's own thinking and learning processes",
    adaptability: "Adjusting to new conditions and challenges",
    selfRegulation: "Managing one's own emotions, thoughts, and behaviors",
    conceptual: "Grasp of theories, principles, and models",
    factual: "Specific details, terminology, and information",
    theoretical: "Understanding of abstract principles and explanatory frameworks",
    methods: "Knowing how to perform specific tasks",
    processes: "Understanding sequences of actions to achieve a goal",
    techniques: "Skillful ways of carrying out a particular task",
    whenToApply: "Knowing when and why to use certain knowledge or skills",
    contextualUse: "Adapting knowledge application to specific situations",
    professionalRole: "Embracing characteristic professional roles and behaviors",
    communityBelonging: "Sense of belonging within the professional community",
    selfEfficacy: "Confidence in professional capabilities",
    dispositions: "Inherent qualities of mind and character (e.g., skepticism, curiosity)",
    coreValues: "Fundamental values like patient well-being, innovation, excellence",
    epistemicValues: "Values related to knowledge and evidence (e.g., empirical evidence, user-centricity)",
    stakeholderValues: "Considering the values and needs of all relevant stakeholders",
    deontological: "Adherence to professional codes and duty-based ethics",
    consequentialist: "Considering outcomes and consequences in decision-making",
    virtue: "Character traits like integrity, responsibility, and honesty",
  };

  useEffect(() => {
    const fetchProfessions = async () => {
      try {
        const res = await fetch('/api/professions');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setProfessions(data);
      } catch (err) {
        console.error('❌ Error loading professions:', err);
        setProfessions([]);
      }
    };
    fetchProfessions();
  }, []);

  useEffect(() => {
    setDepartments([]);
    setSelectedDept('');
    if (selectedProfession) {
      const fetchDepartments = async () => {
        try {
          const res = await fetch(`/api/departments?profession_id=${selectedProfession}`);
          if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
          const data = await res.json();
          setDepartments(data);
        } catch (err) {
          console.error('❌ Error loading departments:', err);
          setDepartments([]);
        }
      };
      fetchDepartments();
    }
  }, [selectedProfession]);

  useEffect(() => {
    setRoles([]);
    setSelectedRole('');
    if (selectedDept) {
      const fetchRoles = async () => {
        try {
          const res = await fetch(`/api/roles?department_id=${selectedDept}`);
          if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
          const data = await res.json();
          setRoles(data);
        } catch (err) {
          console.error('❌ Error loading roles:', err);
          setRoles([]);
        }
      };
      fetchRoles();
    }
  }, [selectedDept]);

  const handleSaveConfig = async () => {
    if (!selectedRole || !profileName) {
      alert('Please select a role and provide a profile name.');
      return;
    }
    try {
      const payload = {
        profession_id: selectedProfession ? parseInt(selectedProfession, 10) : null,
        department_id: selectedDept ? parseInt(selectedDept, 10) : null,
        role_id: parseInt(selectedRole, 10),
        name: profileName,
        skive: skiveRatings,
        day_to_day: dayToDay,
        kras: kras,
      };
      const res = await fetch('/api/config/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Save failed: ${res.statusText}`);
      }
      const result = await res.json();
      console.log('✅ Config saved successfully:', result);
      alert(`Profile saved successfully! Profile ID: ${result.profile_id}`);
    } catch (err: any) {
      console.error('❌ Error saving config:', err);
      alert(`Error saving config: ${err.message}`);
    }
  };

  const generateDayToDay = async () => {
    if (!selectedRole) return;
    try {
      const res = await fetch(`/api/suggestions/day_to_day/${selectedRole}`);
      const data = await res.json();
      setDayToDay(data.suggestions || []);
    } catch (err) {
      console.error('❌ Error generating day-to-day activities:', err);
    }
  };

  const generateKras = async () => {
    if (!selectedRole) return;
    try {
      const res = await fetch(`/api/suggestions/kras/${selectedRole}`);
      const data = await res.json();
      setKras(data.suggestions || []);
    } catch (err) {
      console.error('❌ Error generating KRAs:', err);
    }
  };

  const stage1Props = {
    professions, departments, roles,
    selectedProfession, setSelectedProfession,
    selectedDept, setSelectedDept,
    selectedRole, setSelectedRole,
    profileName, setProfileName,
    dayToDay, setDayToDay,
    kras, setKras,
    skiveRatings, setSkiveRatings,
    competencyDescriptions,
    handleSaveConfig, generateDayToDay, generateKras
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-4 lg:px-6">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Sidebar */}
          <aside className="md:col-span-3 lg:col-span-3">
            {/* ... rest of the code remains the same ... */}
              <div className="px-4 py-3 border-b">
                <h2 className="text-lg font-semibold">PRISM Admin</h2>
                <p className="text-sm text-gray-600">Configure roles and simulations</p>
              </div>
              <nav className="p-2">
                <button
                  onClick={() => setStage('stage1')}
                  className={`w-full text-left px-3 py-2 rounded mb-1 ${stage === 'stage1' ? 'bg-blue-600 text-white' : 'hover:bg-gray-100'}`}
                >
                  Stage 1 • Epistemic Frame
                </button>
                <button
                  onClick={() => setStage('stage2')}
                  className={`w-full text-left px-3 py-2 rounded mb-1 ${stage === 'stage2' ? 'bg-blue-600 text-white' : 'hover:bg-gray-100'}`}
                >
                  Stage 2 • ALE Designer
                </button>
                <button
                  onClick={() => setStage('stage3')}
                  className={`w-full text-left px-3 py-2 rounded ${stage === 'stage3' ? 'bg-blue-600 text-white' : 'hover:bg-gray-100'}`}
                >
                  Stage 3 • Task Factory
                </button>
              </nav>
            </div>
          </aside>

          {/* Main content */}
          <main className="md:col-span-9 lg:col-span-9">
            <div className="bg-white border rounded-lg p-4 md:p-6 relative z-10">
              {stage === 'stage1' && <Stage1 {...stage1Props} />}
              {stage === 'stage2' && <StagePlaceholder title="Stage 2: ALE Designer" />}
              {stage === 'stage3' && <StagePlaceholder title="Stage 3: Task Factory" />}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default PrismAdminApp;