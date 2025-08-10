/**
 * QueryWizard Component - Main step-by-step configuration wizard
 * Orchestrates the 4-step analysis configuration process
 */
import React, { useCallback, useEffect, useState, lazy, Suspense } from 'react';
import { 
  Steps, 
  Card, 
  Button, 
  Row, 
  Col, 
  Typography, 
  Space,
  Alert,
  Divider,
  message,
  Modal,
  Spin
} from 'antd';
import { 
  EnvironmentOutlined,
  AppstoreOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  LeftOutlined,
  RightOutlined,
  PlayCircleOutlined,
  RocketOutlined
} from '@ant-design/icons';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { 
  nextStep, 
  previousStep, 
  setCurrentStep,
  updateConfiguration,
  setSubmitting,
  addActiveJob
} from '@/store/slices/analysisSlice';
import { useSubmitLocationAnalysisMutation } from '@/store/api/analysisApi';

// Lazy load heavy components for better performance
const MapSelector = lazy(() => import('./MapSelector'));
const POICategoryPicker = lazy(() => import('./POICategoryPicker'));
const ParameterSliders = lazy(() => import('./ParameterSliders'));
const TemplateLibrary = lazy(() => import('@/components/templates/TemplateLibrary'));
import type { LocationSearchResult, LocationAnalysisRequest } from '@/types/api';

const { Title, Text } = Typography;
const { Step } = Steps;

interface QueryWizardProps {
  onAnalysisStart?: (jobId: string) => void;
  onComplete?: () => void;
}

// Analysis type options
const ANALYSIS_TYPES = [
  {
    id: 'poi_discovery',
    title: 'Find Places Around Location',
    description: 'Discover what services and amenities are available within travel range of a specific location',
    icon: <EnvironmentOutlined />,
    examples: [
      'What healthcare facilities are within 15 minutes of downtown?',
      'Find all schools accessible by walking from this neighborhood',
      'Map grocery stores within biking distance'
    ],
    popular: true
  },
  {
    id: 'accessibility_analysis', 
    title: 'Analyze Specific Places',
    description: 'Analyze how accessible specific types of places are to the surrounding population',
    icon: <AppstoreOutlined />,
    examples: [
      'How many people can reach hospitals within 20 minutes?',
      'Which libraries serve the most diverse populations?',
      'Analyze transit accessibility to job centers'
    ],
    popular: true
  }
];

// Wizard step configuration
const WIZARD_STEPS = [
  {
    title: 'Location',
    description: 'Select location',
    icon: <EnvironmentOutlined />
  },
  {
    title: 'Analysis Type',
    description: 'Choose analysis type', 
    icon: <AppstoreOutlined />
  },
  {
    title: 'Configure',
    description: 'Set parameters',
    icon: <SettingOutlined />
  },
  {
    title: 'Review & Start',
    description: 'Review and launch',
    icon: <CheckCircleOutlined />
  }
];

/**
 * Main wizard component that orchestrates the analysis configuration process
 */
const QueryWizard: React.FC<QueryWizardProps> = ({ onAnalysisStart, onComplete }) => {
  const dispatch = useAppDispatch();
  const { currentStep, currentConfig, validationErrors, isSubmitting } = useAppSelector(state => state.analysis);
  
  const [selectedLocation, setSelectedLocation] = useState<LocationSearchResult | null>(null);
  const [selectedAnalysisType, setSelectedAnalysisType] = useState<string>('');
  const [templateLibraryVisible, setTemplateLibraryVisible] = useState(false);
  const [submitLocationAnalysis] = useSubmitLocationAnalysisMutation();

  // Validation for each step
  const validateStep = useCallback((step: number): boolean => {
    switch (step) {
      case 0: // Location selection
        return !!currentConfig.location && currentConfig.location.trim() !== '';
      
      case 1: // Analysis type selection  
        return selectedAnalysisType !== '';
      
      case 2: // Configuration
        return !!(
          currentConfig.poi_type && 
          currentConfig.poi_name &&
          currentConfig.travel_time &&
          currentConfig.travel_mode &&
          currentConfig.census_variables?.length
        );
      
      case 3: // Review (always valid if we got here)
        return true;
        
      default:
        return false;
    }
  }, [currentConfig, selectedAnalysisType]);

  // Handle next step
  const handleNext = useCallback(() => {
    if (!validateStep(currentStep)) {
      message.error('Please complete all required fields before continuing');
      return;
    }
    dispatch(nextStep());
  }, [currentStep, dispatch, validateStep]);

  // Handle previous step  
  const handlePrevious = useCallback(() => {
    dispatch(previousStep());
  }, [dispatch]);

  // Handle location selection
  const handleLocationSelect = useCallback((location: LocationSearchResult) => {
    setSelectedLocation(location);
    dispatch(updateConfiguration({ location: location.display_name }));
  }, [dispatch]);

  // Handle analysis type selection
  const handleAnalysisTypeSelect = useCallback((typeId: string) => {
    setSelectedAnalysisType(typeId);
    // Auto-advance to next step after selection
    setTimeout(() => {
      dispatch(nextStep());
    }, 500);
  }, [dispatch]);

  // Start analysis
  const handleStartAnalysis = useCallback(async () => {
    if (!validateStep(2)) {
      message.error('Configuration is incomplete');
      return;
    }

    // Show confirmation modal
    Modal.confirm({
      title: 'Start Analysis',
      content: 'Are you ready to start the analysis? This may take several minutes to complete.',
      okText: 'Start Analysis',
      cancelText: 'Review Settings',
      onOk: async () => {
        try {
          dispatch(setSubmitting(true));

          const analysisRequest: LocationAnalysisRequest = {
            location: currentConfig.location!,
            poi_type: currentConfig.poi_type!,
            poi_name: currentConfig.poi_name!,
            travel_time: currentConfig.travel_time!,
            travel_mode: currentConfig.travel_mode!,
            geographic_level: currentConfig.geographic_level!,
            census_variables: currentConfig.census_variables!,
            include_isochrones: currentConfig.include_isochrones!,
            include_demographics: currentConfig.include_demographics!
          };

          const response = await submitLocationAnalysis(analysisRequest).unwrap();
          
          if (response.success) {
            dispatch(addActiveJob({
              id: response.job_id,
              status: response.status,
              progress: 0,
              created_at: response.created_at,
              updated_at: response.created_at
            }));

            message.success('Analysis started successfully!');
            onAnalysisStart?.(response.job_id);
            onComplete?.();
          }
        } catch (error: any) {
          message.error(`Failed to start analysis: ${error.message || 'Unknown error'}`);
        } finally {
          dispatch(setSubmitting(false));
        }
      }
    });
  }, [currentConfig, dispatch, submitLocationAnalysis, onAnalysisStart, onComplete, validateStep]);

  // Step content renderer
  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <Suspense fallback={
            <Card style={{ textAlign: 'center', padding: '60px 0' }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>Loading map...</div>
            </Card>
          }>
            <MapSelector 
              onLocationSelect={handleLocationSelect}
              selectedLocation={currentConfig.location}
            />
          </Suspense>
        );

      case 1:
        return (
          <div>
            <Title level={4}>Choose Analysis Type</Title>
            <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
              Select the type of analysis you want to perform
            </Text>
            
            <Row gutter={[16, 16]}>
              {ANALYSIS_TYPES.map((type) => (
                <Col xs={24} md={12} key={type.id}>
                  <Card
                    hoverable
                    className={`analysis-type-card ${selectedAnalysisType === type.id ? 'selected' : ''}`}
                    onClick={() => handleAnalysisTypeSelect(type.id)}
                    style={{
                      borderColor: selectedAnalysisType === type.id ? '#1890ff' : undefined,
                      backgroundColor: selectedAnalysisType === type.id ? '#f6ffed' : undefined,
                      cursor: 'pointer'
                    }}
                  >
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ fontSize: '24px', color: '#1890ff' }}>
                          {type.icon}
                        </div>
                        <div>
                          <Title level={5} style={{ margin: 0 }}>
                            {type.title}
                          </Title>
                          {type.popular && (
                            <Text type="secondary" style={{ fontSize: '11px' }}>
                              Most Popular
                            </Text>
                          )}
                        </div>
                      </div>
                      
                      <Text type="secondary">
                        {type.description}
                      </Text>
                      
                      <Divider />
                      
                      <div>
                        <Text strong style={{ fontSize: '12px', color: '#666' }}>
                          Example Use Cases:
                        </Text>
                        <ul style={{ 
                          margin: '8px 0 0 16px', 
                          fontSize: '11px',
                          color: '#999'
                        }}>
                          {type.examples.map((example, idx) => (
                            <li key={idx}>{example}</li>
                          ))}
                        </ul>
                      </div>
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        );

      case 2:
        return (
          <div>
            <Row gutter={16}>
              <Col xs={24} lg={12}>
                <Suspense fallback={
                  <Card style={{ textAlign: 'center', padding: '60px 0' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16 }}>Loading POI selector...</div>
                  </Card>
                }>
                  <POICategoryPicker 
                    onSelectionChange={(types, names) => {
                      dispatch(updateConfiguration({
                        poi_type: types.join(','),
                        poi_name: names.join(',')
                      }));
                    }}
                  />
                </Suspense>
              </Col>
              <Col xs={24} lg={12}>
                <Suspense fallback={
                  <Card style={{ textAlign: 'center', padding: '60px 0' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16 }}>Loading parameters...</div>
                  </Card>
                }>
                  <ParameterSliders 
                    onParameterChange={(config) => {
                      // Already handled by the component
                    }}
                  />
                </Suspense>
              </Col>
            </Row>
          </div>
        );

      case 3:
        return (
          <div>
            <Title level={4}>Review Configuration</Title>
            <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
              Review your analysis settings before starting
            </Text>

            <Card title="Analysis Summary">
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12}>
                  <Text strong>Location:</Text>
                  <br />
                  <Text>{currentConfig.location}</Text>
                </Col>
                
                <Col xs={24} sm={12}>
                  <Text strong>Analysis Type:</Text>
                  <br />
                  <Text>{ANALYSIS_TYPES.find(t => t.id === selectedAnalysisType)?.title}</Text>
                </Col>
                
                <Col xs={24} sm={12}>
                  <Text strong>Places of Interest:</Text>
                  <br />
                  <Text>{currentConfig.poi_name?.split(',').length} types selected</Text>
                </Col>
                
                <Col xs={24} sm={12}>
                  <Text strong>Travel Parameters:</Text>
                  <br />
                  <Text>{currentConfig.travel_time} minutes by {currentConfig.travel_mode}</Text>
                </Col>
                
                <Col xs={24}>
                  <Text strong>Demographic Variables:</Text>
                  <br />
                  <Text>{currentConfig.census_variables?.length} variables selected</Text>
                </Col>
              </Row>
            </Card>

            <Alert
              message="Analysis Ready"
              description="Your configuration is complete. Click 'Start Analysis' to begin processing. This may take 2-5 minutes depending on the complexity."
              type="success"
              showIcon
              style={{ marginTop: 16 }}
            />
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="query-wizard">
      {/* Header with Template Button */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={3} style={{ margin: 0 }}>
            Configure Your Analysis
          </Title>
        </Col>
        <Col>
          <Button
            icon={<RocketOutlined />}
            onClick={() => setTemplateLibraryVisible(true)}
            type="primary"
            ghost
          >
            Use Template
          </Button>
        </Col>
      </Row>

      {/* Progress Steps - Mobile Responsive */}
      <Card style={{ marginBottom: 24 }}>
        <Steps 
          current={currentStep} 
          responsive={true}
          size="small"
          style={{
            '@media (max-width: 576px)': {
              fontSize: '12px'
            }
          }}
        >
          {WIZARD_STEPS.map((step, index) => (
            <Step
              key={index}
              title={<span style={{ fontSize: 'inherit' }}>{step.title}</span>}
              description={window.innerWidth > 576 ? step.description : undefined}
              icon={step.icon}
              status={
                index < currentStep ? 'finish' :
                index === currentStep ? 'process' :
                'wait'
              }
            />
          ))}
        </Steps>
      </Card>

      {/* Step Content - Responsive min-height */}
      <div style={{ 
        minHeight: window.innerWidth > 768 ? '500px' : '400px', 
        marginBottom: 24 
      }}>
        {renderStepContent()}
      </div>

      {/* Navigation Controls - Mobile Friendly */}
      <Card>
        <Row justify="space-between" align="middle" gutter={[8, 8]}>
          <Col xs={8} sm={6}>
            {currentStep > 0 && (
              <Button 
                icon={<LeftOutlined />} 
                onClick={handlePrevious}
                disabled={isSubmitting}
                size={window.innerWidth <= 576 ? 'middle' : 'middle'}
              >
                {window.innerWidth > 576 ? 'Previous' : 'Back'}
              </Button>
            )}
          </Col>
          
          <Col xs={16} sm={18} style={{ textAlign: 'right' }}>
            <Space size={window.innerWidth <= 576 ? 'small' : 'middle'}>
              <Text type="secondary" style={{ 
                fontSize: window.innerWidth <= 576 ? '12px' : '14px',
                display: window.innerWidth <= 400 ? 'none' : 'inline'
              }}>
                Step {currentStep + 1} of {WIZARD_STEPS.length}
              </Text>
              
              {currentStep < WIZARD_STEPS.length - 1 ? (
                <Button 
                  type="primary"
                  icon={<RightOutlined />}
                  iconPosition="end"
                  onClick={handleNext}
                  disabled={!validateStep(currentStep) || isSubmitting}
                  size={window.innerWidth <= 576 ? 'middle' : 'middle'}
                >
                  Next
                </Button>
              ) : (
                <Button
                  type="primary"
                  size={window.innerWidth <= 576 ? 'middle' : 'large'}
                  icon={<PlayCircleOutlined />}
                  loading={isSubmitting}
                  onClick={handleStartAnalysis}
                  disabled={!validateStep(2)}
                >
                  Start Analysis
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Validation Errors */}
      {Object.keys(validationErrors).length > 0 && (
        <Alert
          message="Configuration Issues"
          description={
            <ul>
              {Object.entries(validationErrors).map(([field, error]) => (
                <li key={field}>{error}</li>
              ))}
            </ul>
          }
          type="warning"
          showIcon
          style={{ marginTop: 16 }}
        />
      )}

      {/* Template Library Modal */}
      {templateLibraryVisible && (
        <Suspense fallback={
          <Modal
            open={true}
            footer={null}
            closable={false}
            centered
          >
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>Loading templates...</div>
            </div>
          </Modal>
        }>
          <TemplateLibrary
            onTemplateSelect={(template) => {
              setTemplateLibraryVisible(false);
              message.success(`Template "${template.name}" loaded. Please select a location to begin.`);
            }}
            onClose={() => setTemplateLibraryVisible(false)}
            embedded={false}
          />
        </Suspense>
      )}
    </div>
  );
};

export default QueryWizard;