import React from 'react';
import { BrowserRouter, Routes, Route } from "react-router-dom";

import LoginPage from './pages/LoginPage';
import RegistrationPage from './pages/RegistrationPage';
import DashboardPage from './pages/DashboardPage';
import PrismApp from './pages/PrismApp';

import UserProfileSelectionPage from './pages/UserProfileSelectionPage';
import PathwaySelectionPage from './pages/PathwaySelectionPage';
import ExplorationQuestionsPage from './pages/ExplorationQuestionsPage';
import InterestResultsPage from './pages/InterestResultsPage';
import RolePreviewPage from './pages/RolePreviewPage';
import CareerAssessmentPage from './pages/CareerAssessmentPage';
import Stage3 from './pages/stages/Stage3';


export default function App() {
  return (
    <BrowserRouter>
  <Routes>
    {/* Core pages */}
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegistrationPage />} />
    <Route path="/app" element={<PrismApp />} />
    <Route path="/prism" element={<PrismApp />} />
    <Route path="/dashboard" element={<DashboardPage />} />
    <Route path="/" element={<DashboardPage />} />

    {/* New exploration/assessment flow */}
    <Route path="/select-profile" element={<UserProfileSelectionPage />} />
    <Route path="/select-pathway" element={<PathwaySelectionPage />} />
    <Route path="/exploration-questions" element={<ExplorationQuestionsPage />} />
    <Route path="/interest-results" element={<InterestResultsPage />} />
    <Route path="/role-preview" element={<RolePreviewPage />} />
    <Route path="/career-assessment" element={<CareerAssessmentPage />} />
    <Route path="/stage3" element={<Stage3 />} />
  </Routes>
</BrowserRouter>
  );
}