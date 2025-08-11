import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
const now = new Date().toISOString();
console.log("🕒 Timestamp:", now);

const questions = [
  {
    id: 'cognitive',
    question: 'Do you enjoy solving puzzles or analyzing data?',
    options: ['Not at all', 'Rarely', 'Sometimes', 'Often', 'Very much']
  },
  {
    id: 'metacognitive',
    question: 'Do you enjoy thinking about how you learn and improve?',
    options: ['Not at all', 'Rarely', 'Sometimes', 'Often', 'Very much']
  },
  {
    id: 'behavioral',
    question: 'Do you prefer working in teams or alone?',
    options: ['Strongly prefer alone', 'Somewhat prefer alone', 'No preference', 'Somewhat prefer teams', 'Strongly prefer teams']
  },
  {
    id: 'social',
    question: 'Would you rather spend time networking or researching?',
    options: ['Strongly prefer researching', 'Somewhat prefer researching', 'No preference', 'Somewhat prefer networking', 'Strongly prefer networking']
  },
  {
    id: 'creative',
    question: 'Are you drawn to creative tasks like storytelling or design?',
    options: ['Not at all', 'Rarely', 'Sometimes', 'Often', 'Very much']
  }
];

export default function ExplorationQuestionsPage() {
  const [responses, setResponses] = useState<Record<string, number>>({});
  const navigate = useNavigate();

  const handleChange = (qid: string, index: number) => {
    setResponses(prev => ({ ...prev, [qid]: index }));
  };

   // Ensure this is imported at the top

const handleSubmit = async () => {
  // Map index numbers back to the actual string answers
  const formattedResponses: Record<string, string> = Object.entries(responses).reduce(
    (acc, [qid, selectedIndex]) => {
      const question = questions.find(q => q.id === qid);
      if (question) {
        acc[qid] = question.options[selectedIndex];
      }
      return acc;
    },
    {} as Record<string, string>
  );

  const payload = {
    name: 'Sandeep',
    email: 'sandeep@example.com',
    customer_type: 'student',
    responses: formattedResponses,
  };

  console.log("🚀 Submitting payload:", payload);

  try {
    await axios.post('http://127.0.0.1:8000/api/customers/', payload);
    navigate('/exploration/roles', { state: { responses: formattedResponses } });
  } catch (error) {
    console.error("❌ Error saving customer:", error);
    if (error.response) {
      console.error("🧾 Server said:", error.response.data);
    }
  }
};

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-800 text-center">Tell us about yourself</h1>
      {questions.map((q) => (
        <div key={q.id} className="p-4 bg-white shadow rounded-lg">
          <p className="font-medium text-gray-700 mb-2">{q.question}</p>
          <div className="flex flex-wrap gap-3">
            {q.options.map((opt, index) => (
              <button
                key={index}
                onClick={() => handleChange(q.id, index)}
                className={`px-4 py-2 rounded-full border ${responses[q.id] === index ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      ))}

      <div className="text-center">
        <button
          onClick={handleSubmit}
          disabled={Object.keys(responses).length < questions.length}
          className="px-6 py-3 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50"
        >
          Submit & See Roles
        </button>
      </div>
    </div>
  );
}