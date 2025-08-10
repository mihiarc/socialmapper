/**
 * Interview Request Component - User research interview scheduling
 * Integrates with research team calendar and participant management
 */
import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  Select,
  Button,
  Typography,
  Space,
  Row,
  Col,
  TimePicker,
  Alert,
  Tag,
  Card,
} from 'antd';
import {
  CalendarOutlined,
  UserOutlined,
  MessageOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

import type { InterviewRequest as InterviewRequestType } from '@types/api';
import { useRequestInterviewMutation } from '@store/api/feedbackApi';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface InterviewRequestProps {
  open: boolean;
  onClose: () => void;
  trigger?: 'user_research' | 'usability_feedback' | 'feature_discussion';
}

const INTERVIEW_TYPES = [
  {
    value: 'usability',
    label: 'Usability Testing',
    description: 'Test specific features and identify user experience issues',
    duration: '45-60 minutes',
    icon: <UserOutlined />,
  },
  {
    value: 'feature_discussion',
    label: 'Feature Discussion',
    description: 'Discuss potential new features and improvements',
    duration: '30-45 minutes',
    icon: <MessageOutlined />,
  },
  {
    value: 'workflow_analysis',
    label: 'Workflow Analysis',
    description: 'Understand how SocialMapper fits into your research/work process',
    duration: '45-60 minutes',
    icon: <CalendarOutlined />,
  },
  {
    value: 'general_feedback',
    label: 'General Feedback',
    description: 'Open discussion about your experience with SocialMapper',
    duration: '30-45 minutes',
    icon: <MessageOutlined />,
  },
];

const USER_TYPES = [
  { value: 'academic', label: 'Academic Researcher' },
  { value: 'government', label: 'Government/Public Sector' },
  { value: 'nonprofit', label: 'Non-profit Organization' },
  { value: 'corporate', label: 'Corporate/Private Sector' },
  { value: 'individual', label: 'Individual User' },
];

const TIMEZONE_OPTIONS = [
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Australia/Sydney',
];

const InterviewRequest: React.FC<InterviewRequestProps> = ({
  open,
  onClose,
  trigger,
}) => {
  const [form] = Form.useForm();
  const [selectedInterviewType, setSelectedInterviewType] = useState<string>();
  
  const [requestInterview, { isLoading, error }] = useRequestInterviewMutation();

  const handleSubmit = async (values: any) => {
    try {
      const interviewData: InterviewRequestType = {
        name: values.name,
        email: values.email,
        user_type: values.user_type,
        research_focus: values.research_focus,
        preferred_times: values.preferred_times,
        timezone: values.timezone,
        interview_type: values.interview_type,
      };

      await requestInterview(interviewData).unwrap();
      
      form.resetFields();
      onClose();
      
      // Show success message
      Modal.success({
        title: 'Interview Request Submitted!',
        content: (
          <div>
            <Paragraph>
              Thank you for your interest in participating in user research! 
              Our research team will review your request and contact you within 2-3 business days.
            </Paragraph>
            <Paragraph>
              <Text strong>Next Steps:</Text>
            </Paragraph>
            <ul>
              <li>Check your email for a confirmation message</li>
              <li>Our team will propose specific times based on your preferences</li>
              <li>You'll receive a calendar invitation once scheduled</li>
            </ul>
            <Alert
              type="info"
              showIcon
              message="Your participation helps improve SocialMapper for researchers and planners like you!"
            />
          </div>
        ),
      });
    } catch (error) {
      console.error('Failed to submit interview request:', error);
    }
  };

  const selectedType = INTERVIEW_TYPES.find(type => type.value === selectedInterviewType);

  return (
    <Modal
      title={
        <Space>
          <CalendarOutlined />
          <Title level={4} style={{ margin: 0 }}>
            Request User Research Interview
          </Title>
        </Space>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      width={700}
      destroyOnClose
    >
      <div style={{ marginBottom: '24px' }}>
        <Alert
          type="info"
          showIcon
          message="Help Shape SocialMapper's Future"
          description="Join our user research program to share feedback, test new features, and influence product direction. Interviews are conducted via video call at your convenience."
        />
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          interview_type: trigger || 'general_feedback',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        }}
      >
        {/* Interview Type Selection */}
        <Form.Item
          name="interview_type"
          label="What type of interview interests you?"
          rules={[{ required: true, message: 'Please select an interview type' }]}
        >
          <Select onChange={setSelectedInterviewType}>
            {INTERVIEW_TYPES.map(type => (
              <Option key={type.value} value={type.value}>
                <Space>
                  {type.icon}
                  <div>
                    <Text strong>{type.label}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {type.description}
                    </Text>
                  </div>
                </Space>
              </Option>
            ))}
          </Select>
        </Form.Item>

        {selectedType && (
          <Card size="small" style={{ marginBottom: '16px', background: '#f5f5f5' }}>
            <Row align="middle">
              <Col span={18}>
                <Space>
                  {selectedType.icon}
                  <div>
                    <Text strong>{selectedType.label}</Text>
                    <br />
                    <Text type="secondary">{selectedType.description}</Text>
                  </div>
                </Space>
              </Col>
              <Col span={6}>
                <Tag icon={<ClockCircleOutlined />} color="blue">
                  {selectedType.duration}
                </Tag>
              </Col>
            </Row>
          </Card>
        )}

        {/* Personal Information */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12}>
            <Form.Item
              name="name"
              label="Full Name"
              rules={[
                { required: true, message: 'Please provide your name' },
                { min: 2, message: 'Name must be at least 2 characters' },
              ]}
            >
              <Input placeholder="Your full name" />
            </Form.Item>
          </Col>

          <Col xs={24} sm={12}>
            <Form.Item
              name="email"
              label="Email Address"
              rules={[
                { required: true, message: 'Please provide your email' },
                { type: 'email', message: 'Please enter a valid email address' },
              ]}
            >
              <Input placeholder="your.email@example.com" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="user_type"
          label="How would you describe yourself?"
          rules={[{ required: true, message: 'Please select your user type' }]}
        >
          <Select placeholder="Select your primary role/organization type">
            {USER_TYPES.map(type => (
              <Option key={type.value} value={type.value}>
                {type.label}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="research_focus"
          label="Research Focus or Use Case (Optional)"
        >
          <TextArea
            rows={3}
            placeholder="Briefly describe your research area, projects, or how you use/plan to use SocialMapper"
            maxLength={500}
            showCount
          />
        </Form.Item>

        {/* Scheduling Preferences */}
        <Form.Item
          name="timezone"
          label="Your Timezone"
          rules={[{ required: true, message: 'Please select your timezone' }]}
        >
          <Select showSearch placeholder="Select your timezone">
            {TIMEZONE_OPTIONS.map(tz => (
              <Option key={tz} value={tz}>
                {tz.replace('_', ' ')} - {dayjs().tz(tz).format('HH:mm')}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="preferred_times"
          label="Preferred Interview Times"
          rules={[
            { required: true, message: 'Please provide at least one preferred time' },
            { type: 'array', min: 1, message: 'Please select at least one time slot' },
          ]}
        >
          <Select 
            mode="multiple"
            placeholder="Select 2-3 time slots that work for you"
            maxTagCount={3}
          >
            <Option value="weekday_morning">Weekday Mornings (9AM-12PM)</Option>
            <Option value="weekday_afternoon">Weekday Afternoons (1PM-5PM)</Option>
            <Option value="weekday_evening">Weekday Evenings (6PM-8PM)</Option>
            <Option value="weekend_morning">Weekend Mornings (9AM-12PM)</Option>
            <Option value="weekend_afternoon">Weekend Afternoons (1PM-5PM)</Option>
          </Select>
        </Form.Item>

        {/* Error Display */}
        {error && (
          <Alert
            type="error"
            message="Failed to submit interview request"
            description="Please try again or contact us directly at research@socialmapper.org"
            style={{ marginBottom: '16px' }}
          />
        )}

        {/* Privacy Notice */}
        <div style={{ 
          background: '#f5f5f5', 
          padding: '12px', 
          borderRadius: '6px', 
          marginBottom: '16px' 
        }}>
          <Text style={{ fontSize: '12px' }} type="secondary">
            <strong>Privacy:</strong> Your contact information will only be used for research scheduling 
            and communication. Interview sessions may be recorded (with your consent) for analysis purposes. 
            All data is handled according to our privacy policy and research ethics guidelines.
          </Text>
        </div>

        {/* Form Actions */}
        <Form.Item style={{ marginBottom: 0 }}>
          <Row gutter={[8, 8]} justify="end">
            <Col>
              <Button onClick={onClose}>
                Cancel
              </Button>
            </Col>
            <Col>
              <Button type="primary" htmlType="submit" loading={isLoading}>
                Submit Interview Request
              </Button>
            </Col>
          </Row>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default InterviewRequest;