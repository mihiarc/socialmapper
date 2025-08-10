import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';

import AppLayout from '@components/layout/AppLayout';
import Dashboard from '@pages/Dashboard';
import AnalysisWizard from '@pages/AnalysisWizard';
import Results from '@pages/Results';
import DemoScenarios from '@pages/DemoScenarios';
import PrivacyConsent from '@components/common/PrivacyConsent';

const { Content } = Layout;

/**
 * Main application component with routing configuration
 * Provides the overall app structure and navigation
 */
function App() {
  return (
    <>
      <AppLayout>
        <Content className="app-content">
          <Routes>
            {/* Dashboard - Landing page with overview */}
            <Route path="/" element={<Dashboard />} />
            
            {/* Demo Scenarios - Project 1.1 requirement */}
            <Route path="/demo" element={<DemoScenarios />} />
            
            {/* Analysis Configuration - Main visual configuration interface */}
            <Route path="/analysis" element={<AnalysisWizard />} />
            
            {/* Results Display - Show analysis results and exports */}
            <Route path="/results/:jobId" element={<Results />} />
            
            {/* Job Status and Progress Tracking */}
            <Route path="/jobs/:jobId" element={<Results />} />
          </Routes>
        </Content>
      </AppLayout>
      
      {/* Privacy Consent Management */}
      <PrivacyConsent />
    </>
  );
}

export default App;