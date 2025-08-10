/**
 * Analysis Wizard page - Visual configuration interface
 * Multi-step form for creating custom accessibility analyses
 */
import React from 'react';
import { Typography, Alert } from 'antd';

const { Title, Paragraph } = Typography;

/**
 * Analysis Wizard - Main visual configuration interface
 * TODO: Implement full wizard with QueryWizard, MapSelector, POICategoryPicker components
 */
const AnalysisWizard: React.FC = () => {
  return (
    <div style={{ padding: '24px', minHeight: '100vh', background: '#f5f5f5' }}>
      <Title level={2}>Analysis Wizard</Title>
      <Paragraph>
        Create custom accessibility analyses with our step-by-step configuration interface.
      </Paragraph>
      
      <Alert
        type="info"
        message="Coming Soon"
        description="The full visual configuration wizard is currently under development. This will include interactive map selection, POI category picker, and real-time parameter adjustment."
        style={{ marginTop: '24px' }}
      />
    </div>
  );
};

export default AnalysisWizard;