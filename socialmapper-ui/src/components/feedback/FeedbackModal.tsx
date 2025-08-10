/**
 * Feedback Modal Component - Universal feedback collection interface
 * Supports different feedback types and touchpoints throughout the application
 */
import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  Rate,
  Select,
  Button,
  Typography,
  Space,
  Radio,
  Checkbox,
  Alert,
  Row,
  Col,
} from 'antd';
import {
  StarOutlined,
  BugOutlined,
  BulbOutlined,
  MessageOutlined,
  CloseOutlined,
} from '@ant-design/icons';

import type { 
  FeedbackRequest, 
  FeedbackType, 
  FeedbackTouchpoint 
} from "@/types/api";

const { TextArea } = Input;
const { Text, Title } = Typography;

interface FeedbackModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (feedback: FeedbackRequest) => Promise<void>;
  touchpoint: FeedbackTouchpoint;
  context?: {
    jobId?: string;
    pageUrl?: string;
    featureUsed?: string;
    errorOccurred?: boolean;
  };
  title?: string;
  description?: string;
}

const FEEDBACK_TYPE_OPTIONS = [
  {
    value: 'rating' as FeedbackType,
    label: 'Quick Rating',
    icon: <StarOutlined />,
    description: 'Rate your experience with this feature'
  },
  {
    value: 'usability' as FeedbackType,
    label: 'Usability Feedback',
    icon: <MessageOutlined />,
    description: 'Share thoughts on ease of use and interface'
  },
  {
    value: 'bug_report' as FeedbackType,
    label: 'Report Bug',
    icon: <BugOutlined />,
    description: 'Report an issue or unexpected behavior'
  },
  {
    value: 'feature_request' as FeedbackType,
    label: 'Feature Request',
    icon: <BulbOutlined />,
    description: 'Suggest new features or improvements'
  },
  {
    value: 'general' as FeedbackType,
    label: 'General Feedback',
    icon: <MessageOutlined />,
    description: 'Share any other thoughts or comments'
  }
];

const TOUCHPOINT_TITLES: Record<FeedbackTouchpoint, string> = {
  'post_analysis': 'How was your analysis experience?',
  'configuration_wizard': 'How was the configuration process?',
  'results_dashboard': 'How are the results displayed?',
  'error_state': 'Help us improve error handling',
  'export_download': 'How was the export experience?',
  'general_usage': 'Share your feedback'
};

const FeedbackModal: React.FC<FeedbackModalProps> = ({
  open,
  onClose,
  onSubmit,
  touchpoint,
  context,
  title,
  description,
}) => {
  const [form] = Form.useForm();
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('rating');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const modalTitle = title || TOUCHPOINT_TITLES[touchpoint];

  const handleSubmit = async (values: any) => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const feedbackRequest: FeedbackRequest = {
        type: feedbackType,
        touchpoint,
        rating: values.rating,
        comment: values.comment,
        context: {
          job_id: context?.jobId,
          page_url: context?.pageUrl || window.location.href,
          user_agent: navigator.userAgent,
          session_duration: Math.floor(Date.now() / 1000), // Simple session tracking
          error_occurred: context?.errorOccurred || false,
          feature_used: context?.featureUsed,
        },
        metadata: {
          browser: navigator.userAgent,
          viewport: `${window.innerWidth}x${window.innerHeight}`,
          timestamp: new Date().toISOString(),
        }
      };

      await onSubmit(feedbackRequest);
      form.resetFields();
      onClose();
    } catch (error) {
      setSubmitError('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    form.resetFields();
    setFeedbackType('rating');
    setSubmitError(null);
    onClose();
  };

  return (
    <Modal
      title={modalTitle}
      open={open}
      onCancel={handleClose}
      footer={null}
      width={600}
      closeIcon={<CloseOutlined />}
    >
      <div style={{ marginBottom: '16px' }}>
        {description && (
          <Text type="secondary">{description}</Text>
        )}
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{ rating: 5 }}
      >
        {/* Feedback Type Selection */}
        <Form.Item label="What type of feedback would you like to share?">
          <Radio.Group
            value={feedbackType}
            onChange={(e) => setFeedbackType(e.target.value)}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {FEEDBACK_TYPE_OPTIONS.map((option) => (
                <Radio key={option.value} value={option.value}>
                  <Space>
                    {option.icon}
                    <div>
                      <Text strong>{option.label}</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {option.description}
                      </Text>
                    </div>
                  </Space>
                </Radio>
              ))}
            </Space>
          </Radio.Group>
        </Form.Item>

        {/* Rating for rating and usability feedback */}
        {(feedbackType === 'rating' || feedbackType === 'usability') && (
          <Form.Item
            name="rating"
            label="How would you rate this experience?"
            rules={[{ required: true, message: 'Please provide a rating' }]}
          >
            <Rate allowHalf style={{ fontSize: '24px' }} />
          </Form.Item>
        )}

        {/* Comment Section */}
        <Form.Item
          name="comment"
          label={
            feedbackType === 'bug_report'
              ? 'Describe the issue you encountered'
              : feedbackType === 'feature_request'
              ? 'Describe your feature idea'
              : 'Additional comments (optional)'
          }
          rules={
            feedbackType === 'bug_report' || feedbackType === 'feature_request'
              ? [{ required: true, message: 'Please provide details' }]
              : []
          }
        >
          <TextArea
            rows={4}
            placeholder={
              feedbackType === 'bug_report'
                ? 'Please describe what happened, what you expected, and steps to reproduce the issue...'
                : feedbackType === 'feature_request'
                ? 'Describe the feature you would like to see and how it would help you...'
                : 'Share any additional thoughts or suggestions...'
            }
            maxLength={1000}
            showCount
          />
        </Form.Item>

        {/* Error Display */}
        {submitError && (
          <Alert
            type="error"
            message="Submission Failed"
            description={submitError}
            style={{ marginBottom: '16px' }}
          />
        )}

        {/* Form Actions */}
        <Form.Item style={{ marginBottom: 0 }}>
          <Row gutter={[8, 8]} justify="end">
            <Col>
              <Button onClick={handleClose}>
                Cancel
              </Button>
            </Col>
            <Col>
              <Button
                type="primary"
                htmlType="submit"
                loading={isSubmitting}
              >
                Submit Feedback
              </Button>
            </Col>
          </Row>
        </Form.Item>
      </Form>

      {/* Privacy Notice */}
      <div style={{ marginTop: '16px', padding: '12px', background: '#f5f5f5', borderRadius: '4px' }}>
        <Text style={{ fontSize: '12px' }} type="secondary">
          Your feedback helps us improve SocialMapper. We collect minimal data needed for improvement and never share personal information. 
          You can provide feedback anonymously.
        </Text>
      </div>
    </Modal>
  );
};

export default FeedbackModal;