// src/pages/PrismApp.tsx

import React, { useState, useEffect } from 'react';
import type { FC, MouseEvent, KeyboardEvent, ChangeEvent } from 'react';
import { Save, Sparkles, ListChecks, ClipboardList, ChevronDown } from 'lucide-react';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';
import Stage2 from './stages/Stage2';
import Stage3 from './stages/Stage3';
import { useProfessions, useDepartments, useRoles } from '../api/client';

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

// --- STAGE 2 TYPES ---
interface ObjectiveLevels {
  basic: string;
  intermediate: string;
  advanced: string;
}
type ObjectiveSource = 'none' | 'ai' | 'default';
type ObjectivesMap = Record<string, ObjectiveLevels & { source: ObjectiveSource }>; // key: path like skills.cognitive.analytical

interface Stage1Props {
  professions: SelectOption[];
  departments: SelectOption[];
  roles: SelectOption[];
  selectedProfession: string;
  setSelectedProfession: (value: string) => void;
  selectedDept: string;
  setSelectedDept: (value: string) => void;
  selectedRole: string;
  setSelectedRole: (value: string) => void;
  profileName: string;
  setProfileName: (value: string) => void;
  dayToDay: string[];
  setDayToDay: (value: string[]) => void;
  kras: string[];
  setKras: (value: string[]) => void;
  dayToDaySource: 'default' | 'ai' | 'none';
  krasSource: 'default' | 'ai' | 'none';
  skiveRatings: SkiveRatings;
  setSkiveRatings: (value: SkiveRatings | ((prev: SkiveRatings) => SkiveRatings)) => void;
  competencyDescriptions: Record<string, string>;
  handleSaveConfig: () => void;
  generateDayToDay: () => void;
  generateKras: () => void;
}

// --- REUSABLE CHILD COMPONENTS ---

const AccordionItem: FC<AccordionItemProps> = ({ label, children, defaultOpen = true }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  const handleToggle = () => {
    setIsOpen(prev => !prev);
  };

// (Stage2 extracted into separate component)

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



const Stage1: FC<Stage1Props> = ({
  professions, departments, roles,
  selectedProfession, setSelectedProfession,
  selectedDept, setSelectedDept,
  selectedRole, setSelectedRole,
  profileName, setProfileName,
  dayToDay, setDayToDay,
  kras, setKras,
  dayToDaySource, krasSource,
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

    // Extract values correctly from nested SKIVE structure
    const skillsVals = Object.values(skiveRatings.skills).flatMap(subcategory => Object.values(subcategory));
    const knowledgeVals = Object.values(skiveRatings.knowledge).flatMap(subcategory => Object.values(subcategory));
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
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Profile Name <span className="text-red-500">*</span></label>
            <input
              type="text"
              value={profileName}
              onChange={(e) => setProfileName(e.target.value)}
              placeholder="Enter a name for this role profile..."
              required
              className="w-full p-2 border rounded bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <button onClick={generateDayToDay} className="flex items-center gap-2 text-sm text-blue-600 hover:underline"><Sparkles size={14} /> Generate Day-to-Day Activities</button>
                {dayToDaySource !== 'none' && (
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                    dayToDaySource === 'ai' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
                  }`}>
                    {dayToDaySource === 'ai' ? '🤖 AI Generated' : '📋 Default Values'}
                  </div>
                )}
              </div>
              <EditableList items={dayToDay} onChange={setDayToDay} title="Day-to-Day Activities" icon={<ListChecks size={20} />} />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <button onClick={generateKras} className="flex items-center gap-2 text-sm text-blue-600 hover:underline"><Sparkles size={14} /> Generate KRAs</button>
                {krasSource !== 'none' && (
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                    krasSource === 'ai' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                      : 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
                  }`}>
                    {krasSource === 'ai' ? '🤖 AI Generated' : '📋 Default Values'}
                  </div>
                )}
              </div>
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
                      // For skills/knowledge: subCategory is like 'cognitive', items is { analytical: 1, decisionMaking: 1, ... }
                      // For identity/values/ethics: subCategory is like 'professionalRole', items is just the number 1
                      const isSimple = typeof items === 'number';
                      console.log(`Category: ${mainCategory}.${subCategory}, Items:`, items, 'Is simple:', isSimple);
                      if (isSimple) {
                        return (
                          <div key={subCategory} className="p-4 bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700">
                            <h4 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">{subCategory.replace(/([A-Z])/g, ' $1')}</h4>
                            <p className="mb-2 text-xs text-gray-500 dark:text-gray-400">{competencyDescriptions[`${mainCategory}.${subCategory}`] || 'No description available.'}</p>
                            <RangeWithTicks value={items as unknown as number} onChange={(newValue) => handleSimpleSkiveChange(mainCategory as keyof SkiveRatings, subCategory, newValue)} />
                          </div>
                        );
                      }
                      return (
                        <AccordionItem key={subCategory} label={subCategory.charAt(0).toUpperCase() + subCategory.slice(1)} defaultOpen={false}>
                          <div className="p-4 space-y-3 bg-gray-100 dark:bg-gray-800">
                            {Object.entries(items as Record<string, number>).map(([item, value]) => (
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

          {/* Submit Button */}
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700 flex justify-center">
            <button
              onClick={handleSaveConfig}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors duration-200 flex items-center gap-2"
            >
              <Save className="w-5 h-5" />
              Save Profile
            </button>
          </div>

          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-center mb-2">Overall SKIVE Radar</h3>
            <div className="flex justify-center">
              <RadarChart cx={300} cy={150} outerRadius={100} width={600} height={300} data={radarData()}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" />
              <PolarRadiusAxis angle={30} domain={[0, 10]} />
              <Radar name="SKIVE" dataKey="A" stroke="#2563eb" fill="#2563eb" fillOpacity={0.4} />
              </RadarChart>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// --- MAIN APP COMPONENT ---

const PrismAdminApp: FC = () => {
  const [stage, setStage] = useState<Stage>('stage1');
  const [selectedProfession, setSelectedProfession] = useState<string>('');
  const [selectedDept, setSelectedDept] = useState<string>('');
  const [selectedRole, setSelectedRole] = useState<string>('');
  const { data: professionsData = [] } = useProfessions();
  const { data: departmentsData = [] } = useDepartments(selectedProfession || undefined);
  const { data: rolesData = [] } = useRoles(selectedDept || undefined);
  const [profileName, setProfileName] = useState<string>('');
  const [dayToDay, setDayToDay] = useState<string[]>([]);
  const [kras, setKras] = useState<string[]>([]);
  const [dayToDaySource, setDayToDaySource] = useState<'default' | 'ai' | 'none'>('none');
  const [krasSource, setKrasSource] = useState<'default' | 'ai' | 'none'>('none');
  // Stage 2 state: objectives per sub-competency
  const [objectives, setObjectives] = useState<ObjectivesMap>({});
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
    "identity.professionalRole": "Embracing characteristic professional roles and behaviors",
    "identity.communityBelonging": "Sense of belonging within the professional community",
    "identity.selfEfficacy": "Confidence in professional capabilities",
    "identity.dispositions": "Inherent qualities of mind and character (e.g., skepticism, curiosity)",
    "values.coreValues": "Fundamental values like patient well-being, innovation, excellence",
    "values.epistemicValues": "Values related to knowledge and evidence (e.g., empirical evidence, user-centricity)",
    "values.stakeholderValues": "Considering the values and needs of all relevant stakeholders",
    "ethics.deontological": "Adherence to professional codes and duty-based ethics",
    "ethics.consequentialist": "Considering outcomes and consequences in decision-making",
    "ethics.virtue": "Character traits like integrity, responsibility, and honesty",
  };

  // Reset dependent selections when parent changes
  useEffect(() => { setSelectedDept(''); }, [selectedProfession]);
  useEffect(() => { setSelectedRole(''); }, [selectedDept]);

  const handleSaveConfig = async () => {
    if (!selectedRole || !profileName.trim()) {
      alert('Please select a role and provide a profile name.');
      return;
    }
    try {
      const payload = {
        profession: selectedProfession ? parseInt(selectedProfession, 10) : null,
        department: selectedDept ? parseInt(selectedDept, 10) : null,
        role: parseInt(selectedRole, 10),
        name: profileName,
        skive: skiveRatings,
        day_to_day: dayToDay,
        kras: kras,
        objectives,
      };
      const res = await fetch('/api/config/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errorText = await res.text();
        let errorMessage = `Save failed: ${res.statusText}`;
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch {
          errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
      }
      const result = await res.json();
      console.log('✅ Config saved successfully:', result);
      // Show success message in a more user-friendly way
      const successMessage = document.createElement('div');
      successMessage.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
      successMessage.innerHTML = `✅ Profile "${profileName}" saved successfully!`;
      document.body.appendChild(successMessage);
      setTimeout(() => {
        if (successMessage.parentNode) {
          successMessage.parentNode.removeChild(successMessage);
        }
      }, 3000);
    } catch (err: any) {
      console.error('❌ Error saving config:', err);
      alert(`❌ Error saving profile: ${err.message}`);
    }
  };

  const generateDayToDay = async () => {
    if (!selectedRole) {
      alert('Please select a role first.');
      return;
    }
    // Only generate if dayToDay is empty or user confirms
    if (dayToDay.length > 0) {
      const confirmed = confirm('This will replace existing day-to-day activities. Continue?');
      if (!confirmed) return;
    }
    
    console.log('🚀 Starting day-to-day generation...');
    
    try {
      const payload = {
        profession: selectedProfession ? parseInt(selectedProfession, 10) : null,
        department: selectedDept ? parseInt(selectedDept, 10) : null,
        role: parseInt(selectedRole, 10)
      };
      
      console.log('📤 Sending payload to /api/ai/day_to_day:', payload);
      
      const res = await fetch('/api/ai/day_to_day', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      console.log('📥 Response status:', res.status, res.statusText);
      
      if (res.ok) {
        const data = await res.json();
        console.log('📋 Raw response data:', data);
        
        const activities = data.items || data.suggestions || [];
        setDayToDay(activities);
        
        // Use source field from backend response
        const source = data.source || 'default';
        setDayToDaySource(source);
        
        console.log(`✅ Day-to-day activities generated from ${source === 'ai' ? 'Gemini AI' : 'Default Logic'}:`, activities);
      } else {
        console.error('❌ Failed to generate day-to-day activities:', res.status, res.statusText);
        const errorText = await res.text();
        console.error('❌ Error response:', errorText);
        alert('Failed to generate day-to-day activities. Please try again.');
        setDayToDaySource('default');
      }
    } catch (err) {
      console.error('❌ Error generating day-to-day activities:', err);
      alert('Error generating day-to-day activities. Please check your connection.');
      setDayToDaySource('default');
    }
  };

  const generateKras = async () => {
    if (!selectedRole) {
      alert('Please select a role first.');
      return;
    }
    // Only generate if kras is empty or user confirms
    if (kras.length > 0) {
      const confirmed = confirm('This will replace existing KRAs. Continue?');
      if (!confirmed) return;
    }
    
    console.log('🚀 Starting KRAs generation...');
    
    try {
      const payload = {
        profession: selectedProfession ? parseInt(selectedProfession, 10) : null,
        department: selectedDept ? parseInt(selectedDept, 10) : null,
        role: parseInt(selectedRole, 10)
      };
      
      console.log('📤 Sending payload to /api/ai/kras:', payload);
      
      const res = await fetch('/api/ai/kras', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      console.log('📥 Response status:', res.status, res.statusText);
      
      if (res.ok) {
        const data = await res.json();
        console.log('📋 Raw response data:', data);
        
        const krasList = data.items || data.suggestions || [];
        setKras(krasList);
        
        // Use source field from backend response
        const source = data.source || 'default';
        setKrasSource(source);
        
        console.log(`✅ KRAs generated from ${source === 'ai' ? 'Gemini AI' : 'Default Logic'}:`, krasList);
      } else {
        console.error('❌ Failed to generate KRAs:', res.status, res.statusText);
        const errorText = await res.text();
        console.error('❌ Error response:', errorText);
        alert('Failed to generate KRAs. Please try again.');
        setKrasSource('default');
      }
    } catch (err) {
      console.error('❌ Error generating KRAs:', err);
      alert('Error generating KRAs. Please check your connection.');
      setKrasSource('default');
    }
  };

  // Helper function for calculating averages
  const avg = (values: number[]): number => {
    if (values.length === 0) return 0;
    return values.reduce((sum, val) => sum + val, 0) / values.length;
  };

  // Function to generate radar chart data
  const radarData = () => {
    const skillsVals = Object.values(skiveRatings.skills).flatMap(subcategory => Object.values(subcategory));
    const knowledgeVals = Object.values(skiveRatings.knowledge).flatMap(subcategory => Object.values(subcategory));
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

  // Function to get comprehensive SKIVE data for Stage 3
  const getSkiveDataForStage3 = () => {
    const skillsVals = Object.values(skiveRatings.skills).flatMap(subcategory => Object.values(subcategory));
    const knowledgeVals = Object.values(skiveRatings.knowledge).flatMap(subcategory => Object.values(subcategory));
    const identityVals = Object.values(skiveRatings.identity);
    const valuesVals = Object.values(skiveRatings.values);
    const ethicsVals = Object.values(skiveRatings.ethics);
    
    const radarChartData = radarData();

    return {
      rawSkiveRatings: skiveRatings,
      radarChartData,
      categoryAverages: {
        skills: radarChartData.find((item: any) => item.subject === 'Skills')?.A || 0,
        knowledge: radarChartData.find((item: any) => item.subject === 'Knowledge')?.A || 0,
        identity: radarChartData.find((item: any) => item.subject === 'Identity')?.A || 0,
        values: radarChartData.find((item: any) => item.subject === 'Values')?.A || 0,
        ethics: radarChartData.find((item: any) => item.subject === 'Ethics')?.A || 0,
      },
      flattenedSkiveValues: {
        skills: skillsVals,
        knowledge: knowledgeVals,
        identity: identityVals,
        values: valuesVals,
        ethics: ethicsVals,
      }
    };
  };

  

  // Handler for complex SKIVE changes (skills/knowledge with nested structure)
  const handleSkiveChange = (category: keyof SkiveRatings, subCategory: string, item: string, value: number) => {
    setSkiveRatings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [subCategory]: {
          ...(prev[category] as any)[subCategory],
          [item]: value
        }
      }
    }));
  };

  // Handler for simple SKIVE changes (identity/values/ethics with direct values)
  const handleSimpleSkiveChange = (category: keyof SkiveRatings, subCategory: string, value: number) => {
    setSkiveRatings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [subCategory]: value
      }
    }));
  };

  const professions = professionsData;
  const departments = departmentsData;
  const roles = rolesData;
  const stage1Props = {
    professions, departments, roles,
    selectedProfession, setSelectedProfession,
    selectedDept, setSelectedDept,
    selectedRole, setSelectedRole,
    profileName, setProfileName,
    dayToDay, setDayToDay,
    kras, setKras,
    dayToDaySource, krasSource,
    skiveRatings, setSkiveRatings,
    competencyDescriptions,
    handleSaveConfig, generateDayToDay, generateKras,
    handleSkiveChange, handleSimpleSkiveChange, radarData
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-4 lg:px-6">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Sidebar */}
          <aside className="md:col-span-3 lg:col-span-3">
            <div className="bg-white border rounded-lg">
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
                  Stage 2 • Simulation Objectives
                </button>
                <button
                  onClick={() => setStage('stage3')}
                  className={`w-full text-left px-3 py-2 rounded ${stage === 'stage3' ? 'bg-blue-600 text-white' : 'hover:bg-gray-100'}`}
                >
                  Stage 3 • Archetypes DNA
                </button>
              </nav>
            </div>
          </aside>

          {/* Main content */}
          <main className="md:col-span-9 lg:col-span-9">
            <div className="bg-white border rounded-lg p-4 md:p-6 relative z-10">
              {stage === 'stage1' && <Stage1 {...stage1Props} />}
              {stage === 'stage2' && (
                <Stage2
                  objectives={objectives}
                  setObjectives={setObjectives}
                  skiveRatings={skiveRatings}
                  selectedProfession={selectedProfession}
                  selectedDept={selectedDept}
                  selectedRole={selectedRole}
                />
              )}
              {stage === 'stage3' &&
  selectedProfession && selectedDept && selectedRole && getSkiveDataForStage3() ? (
    <Stage3
      profileId={1} // TODO: replace with real profile ID if available
      profession={parseInt(selectedProfession, 10)}
      department={parseInt(selectedDept, 10)}
      role={parseInt(selectedRole, 10)}
      skiveData={{
        skills: Object.fromEntries(
          Object.entries(skiveRatings.skills).flatMap(([sub, items]) =>
            Object.entries(items as Record<string, number>).map(([k, v]) => [k, v])
          )
        ),
        knowledge: Object.fromEntries(
          Object.entries(skiveRatings.knowledge).flatMap(([sub, items]) =>
            Object.entries(items as Record<string, number>).map(([k, v]) => [k, v])
          )
        ),
        identity: skiveRatings.identity,
        values: skiveRatings.values,
        ethics: skiveRatings.ethics,
        combined: {
          Skills: (() => {
            const vals = Object.values(skiveRatings.skills).flatMap(sub => Object.values(sub));
            return vals.length > 0 ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
          })(),
          Knowledge: (() => {
            const vals = Object.values(skiveRatings.knowledge).flatMap(sub => Object.values(sub));
            return vals.length > 0 ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
          })(),
          Identity: (() => {
            const vals = Object.values(skiveRatings.identity);
            return vals.length > 0 ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
          })(),
          Values: (() => {
            const vals = Object.values(skiveRatings.values);
            return vals.length > 0 ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
          })(),
          Ethics: (() => {
            const vals = Object.values(skiveRatings.ethics);
            return vals.length > 0 ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
          })(),
        }
      }}
      professionName={(professions.find(p => String(p.id) === selectedProfession)?.name) || undefined}
      departmentName={(departments.find(d => String(d.id) === selectedDept)?.name) || undefined}
      roleName={(roles.find(r => String(r.id) === selectedRole)?.name) || undefined}
    />
  ) : (
    <div className="p-6 text-gray-500">Please complete Stage 1 and 2 to view your Role DNA Archetype.</div>
  )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default PrismAdminApp;