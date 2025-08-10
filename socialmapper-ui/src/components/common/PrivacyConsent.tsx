/**
 * Privacy Consent Component - GDPR/CCPA compliant consent management
 * Handles user consent for analytics, feedback, and data collection
 */
import React, { useState, useEffect } from 'react';
import {
  Modal,
  Alert,
  Button,
  Typography,
  Space,
  Checkbox,
  Divider,
  Row,
  Col,
  Card,
} from 'antd';
import {
  SecurityScanOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

interface PrivacyConsentProps {
  onConsentChange?: (consents: ConsentSettings) => void;
}

interface ConsentSettings {
  analytics: boolean;
  feedback: boolean;
  functional: boolean; // Always true for essential functionality
  marketing: boolean;
}

const CONSENT_STORAGE_KEY = 'socialmapper_consent_settings';
const CONSENT_VERSION = '1.0';
const CONSENT_VERSION_KEY = 'socialmapper_consent_version';

const PrivacyConsent: React.FC<PrivacyConsentProps> = ({ onConsentChange }) => {
  const [showModal, setShowModal] = useState(false);
  const [consents, setConsents] = useState<ConsentSettings>({
    analytics: false,
    feedback: false,
    functional: true,
    marketing: false,
  });

  // Check if consent is needed
  useEffect(() => {
    const storedConsents = localStorage.getItem(CONSENT_STORAGE_KEY);
    const storedVersion = localStorage.getItem(CONSENT_VERSION_KEY);
    
    if (!storedConsents || storedVersion !== CONSENT_VERSION) {
      setShowModal(true);
    } else {
      const parsedConsents = JSON.parse(storedConsents);
      setConsents(parsedConsents);
      if (onConsentChange) {
        onConsentChange(parsedConsents);
      }
    }
  }, [onConsentChange]);

  const handleConsentChange = (type: keyof ConsentSettings, value: boolean) => {
    const newConsents = { ...consents, [type]: value };
    setConsents(newConsents);
  };

  const saveConsents = (consentSettings: ConsentSettings) => {
    localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(consentSettings));
    localStorage.setItem(CONSENT_VERSION_KEY, CONSENT_VERSION);
    
    // Set specific consent flags for easy access
    localStorage.setItem('socialmapper_analytics_consent', consentSettings.analytics ? 'granted' : 'denied');
    localStorage.setItem('socialmapper_feedback_consent', consentSettings.feedback ? 'granted' : 'denied');
    localStorage.setItem('socialmapper_marketing_consent', consentSettings.marketing ? 'granted' : 'denied');
    
    if (onConsentChange) {
      onConsentChange(consentSettings);
    }
    setShowModal(false);
  };

  const handleAcceptAll = () => {
    const allConsents = {
      analytics: true,
      feedback: true,
      functional: true,
      marketing: false, // Keep marketing false by default
    };
    saveConsents(allConsents);
  };

  const handleAcceptSelected = () => {
    saveConsents(consents);
  };

  const handleDeclineAll = () => {
    const minimalConsents = {
      analytics: false,
      feedback: false,
      functional: true, // Always required
      marketing: false,
    };
    saveConsents(minimalConsents);
  };

  if (!showModal) {
    return null;
  }

  return (
    <Modal
      title={
        <Space>
          <SecurityScanOutlined />
          <Title level={4} style={{ margin: 0 }}>
            Privacy & Data Collection
          </Title>
        </Space>
      }
      open={showModal}
      footer={null}
      closable={false}
      maskClosable={false}
      width={700}
    >
      <div style={{ marginBottom: '24px' }}>
        <Alert
          type="info"
          showIcon
          message="Help us improve SocialMapper while protecting your privacy"
          description="We believe in transparent data practices. Choose what data you're comfortable sharing to help us improve the platform."
          style={{ marginBottom: '16px' }}
        />

        <Paragraph>
          SocialMapper is committed to your privacy. We collect only the minimum data needed to provide 
          and improve our service. You have full control over what data is collected.
        </Paragraph>
      </div>

      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Essential/Functional */}
        <Card size="small">
          <Row align="middle">
            <Col flex="auto">
              <Space direction="vertical" size="small">
                <Text strong>
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: '8px' }} />
                  Essential Functionality
                </Text>
                <Text type="secondary" style={{ fontSize: '14px' }}>
                  Required for the platform to work properly. Includes session management, 
                  security features, and basic error reporting.
                </Text>
              </Space>
            </Col>
            <Col>
              <Text type="secondary">Always Active</Text>
            </Col>
          </Row>
        </Card>

        {/* Analytics */}
        <Card size="small">
          <Row align="middle">
            <Col flex="auto">
              <Space direction="vertical" size="small">
                <Text strong>
                  <Checkbox
                    checked={consents.analytics}
                    onChange={(e) => handleConsentChange('analytics', e.target.checked)}
                  >
                    Usage Analytics
                  </Checkbox>
                </Text>
                <Text type="secondary" style={{ fontSize: '14px' }}>
                  Anonymous data about how you use the platform to help us improve user experience. 
                  Includes page views, feature usage, and performance metrics.
                </Text>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Feedback */}
        <Card size="small">
          <Row align="middle">
            <Col flex="auto">
              <Space direction="vertical" size="small">
                <Text strong>
                  <Checkbox
                    checked={consents.feedback}
                    onChange={(e) => handleConsentChange('feedback', e.target.checked)}
                  >
                    Feedback & Improvements
                  </Checkbox>
                </Text>
                <Text type="secondary" style={{ fontSize: '14px' }}>
                  Collect feedback you provide through surveys and feedback forms to improve features. 
                  Helps us understand what works well and what needs improvement.
                </Text>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Marketing/Communications */}
        <Card size="small">
          <Row align="middle">
            <Col flex="auto">
              <Space direction="vertical" size="small">
                <Text strong>
                  <Checkbox
                    checked={consents.marketing}
                    onChange={(e) => handleConsentChange('marketing', e.target.checked)}
                  >
                    Community & Updates
                  </Checkbox>
                </Text>
                <Text type="secondary" style={{ fontSize: '14px' }}>
                  Occasionally share updates about new features, research opportunities, 
                  and community events. No third-party marketing ever.
                </Text>
              </Space>
            </Col>
          </Row>
        </Card>
      </Space>

      <Divider />

      <div style={{ marginBottom: '16px' }}>
        <Space>
          <InfoCircleOutlined style={{ color: '#1890ff' }} />
          <Text style={{ fontSize: '12px' }} type="secondary">
            You can change these preferences at any time in Settings. 
            We never sell or share your data with third parties.
          </Text>
        </Space>
      </div>

      {/* Action Buttons */}
      <Row gutter={[12, 12]}>
        <Col xs={24} sm={8}>
          <Button block onClick={handleDeclineAll}>
            Essential Only
          </Button>
        </Col>
        <Col xs={24} sm={8}>
          <Button type="primary" block onClick={handleAcceptSelected}>
            Accept Selected
          </Button>
        </Col>
        <Col xs={24} sm={8}>
          <Button type="primary" block onClick={handleAcceptAll}>
            Accept All
          </Button>
        </Col>
      </Row>

      <div style={{ marginTop: '16px', fontSize: '12px', color: '#666' }}>
        <Text type="secondary">
          By using SocialMapper, you agree to our{' '}
          <a href="/privacy-policy" target="_blank" rel="noopener noreferrer">
            Privacy Policy
          </a>{' '}
          and{' '}
          <a href="/terms-of-service" target="_blank" rel="noopener noreferrer">
            Terms of Service
          </a>
          . Data is processed according to GDPR and CCPA guidelines.
        </Text>
      </div>
    </Modal>
  );
};

export default PrivacyConsent;