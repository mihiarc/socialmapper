/**
 * Analysis Wizard page - Visual configuration interface
 * Multi-step form for creating custom accessibility analyses
 */
import React, { useCallback } from 'react';
import { Typography, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import QueryWizard from '@/components/wizard/QueryWizard';

const { Title, Paragraph } = Typography;

/**
 * Analysis Wizard - Main visual configuration interface
 * Full wizard implementation with QueryWizard, MapSelector, POICategoryPicker components
 */
const AnalysisWizard: React.FC = () => {
  const navigate = useNavigate();

  // Handle when analysis starts successfully
  const handleAnalysisStart = useCallback((jobId: string) => {
    // Navigate to job status page 
    navigate(`/jobs/${jobId}`);
  }, [navigate]);

  // Handle wizard completion (analysis submitted)
  const handleWizardComplete = useCallback(() => {
    message.success('Analysis submitted successfully! You can monitor progress and view results when complete.');
  }, []);

  return (
    <div style={{ padding: '24px', minHeight: '100vh', background: '#f5f5f5' }}>
      <div style={{ marginBottom: '32px' }}>
        <Title level={2}>Analysis Wizard</Title>
        <Paragraph>
          Create custom accessibility analyses with our step-by-step configuration interface.
          Select locations, choose points of interest, configure parameters, and launch your analysis.
        </Paragraph>
      </div>
      
      <QueryWizard 
        onAnalysisStart={handleAnalysisStart}
        onComplete={handleWizardComplete}
      />
    </div>
  );
};

export default AnalysisWizard;