/**
 * Feedback Trigger Component - Contextual feedback collection triggers
 * Can be embedded throughout the application for targeted feedback collection
 */
import React, { useState } from 'react';
import { Button, Tooltip, FloatButton } from 'antd';
import {
  MessageOutlined,
  StarOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons';

import FeedbackModal from './FeedbackModal';
import type { FeedbackTouchpoint, FeedbackRequest } from "@/types/api";
import { useSubmitFeedbackMutation } from '@store/api/feedbackApi';

interface FeedbackTriggerProps {
  touchpoint: FeedbackTouchpoint;
  context?: {
    jobId?: string;
    featureUsed?: string;
    errorOccurred?: boolean;
  };
  
  // Display options
  trigger?: 'button' | 'float' | 'inline' | 'auto';
  size?: 'small' | 'middle' | 'large';
  type?: 'primary' | 'default' | 'dashed' | 'text' | 'link';
  icon?: React.ReactNode;
  text?: string;
  tooltip?: string;
  
  // Auto-trigger options (for post-analysis, error states, etc.)
  autoTrigger?: boolean;
  autoTriggerDelay?: number; // milliseconds
  
  // Customization
  title?: string;
  description?: string;
  
  // Callbacks
  onFeedbackSubmit?: (feedback: FeedbackRequest) => void;
}

const TOUCHPOINT_CONFIG = {
  post_analysis: {
    defaultText: 'How was this analysis?',
    defaultTooltip: 'Share feedback about your analysis experience',
    defaultIcon: <StarOutlined />,
    autoDelay: 2000,
  },
  configuration_wizard: {
    defaultText: 'Give Feedback',
    defaultTooltip: 'Help us improve the configuration process',
    defaultIcon: <MessageOutlined />,
    autoDelay: 0,
  },
  results_dashboard: {
    defaultText: 'Rate Results',
    defaultTooltip: 'How helpful are these results?',
    defaultIcon: <StarOutlined />,
    autoDelay: 5000,
  },
  error_state: {
    defaultText: 'Report Issue',
    defaultTooltip: 'Help us fix this problem',
    defaultIcon: <QuestionCircleOutlined />,
    autoDelay: 1000,
  },
  export_download: {
    defaultText: 'Rate Export',
    defaultTooltip: 'How was the export experience?',
    defaultIcon: <StarOutlined />,
    autoDelay: 3000,
  },
  general_usage: {
    defaultText: 'Feedback',
    defaultTooltip: 'Share your thoughts',
    defaultIcon: <MessageOutlined />,
    autoDelay: 0,
  },
};

const FeedbackTrigger: React.FC<FeedbackTriggerProps> = ({
  touchpoint,
  context,
  trigger = 'button',
  size = 'middle',
  type = 'default',
  icon,
  text,
  tooltip,
  autoTrigger = false,
  autoTriggerDelay,
  title,
  description,
  onFeedbackSubmit,
}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [hasAutoTriggered, setHasAutoTriggered] = useState(false);
  const [submitFeedback, { isLoading }] = useSubmitFeedbackMutation();

  const config = TOUCHPOINT_CONFIG[touchpoint];
  const displayText = text || config.defaultText;
  const displayTooltip = tooltip || config.defaultTooltip;
  const displayIcon = icon || config.defaultIcon;
  const triggerDelay = autoTriggerDelay ?? config.autoDelay;

  // Auto-trigger logic
  React.useEffect(() => {
    if (autoTrigger && !hasAutoTriggered && triggerDelay >= 0) {
      const timer = setTimeout(() => {
        setModalOpen(true);
        setHasAutoTriggered(true);
      }, triggerDelay);

      return () => clearTimeout(timer);
    }
  }, [autoTrigger, hasAutoTriggered, triggerDelay]);

  const handleFeedbackSubmit = async (feedback: FeedbackRequest) => {
    try {
      // Submit to feedback API
      await submitFeedback(feedback).unwrap();
      
      // Call the callback if provided
      if (onFeedbackSubmit) {
        onFeedbackSubmit(feedback);
      }

      // Show success notification (you might want to use a notification system)
      console.log('Feedback submitted successfully:', feedback);

    } catch (error) {
      console.error('Failed to submit feedback:', error);
      throw error; // Re-throw so modal can handle the error
    }
  };

  const triggerButton = (
    <Button
      type={type}
      size={size}
      icon={displayIcon}
      onClick={() => setModalOpen(true)}
    >
      {displayText}
    </Button>
  );

  const renderTrigger = () => {
    switch (trigger) {
      case 'float':
        return (
          <FloatButton
            icon={displayIcon}
            tooltip={displayTooltip}
            onClick={() => setModalOpen(true)}
            style={{ right: 24, bottom: 24 }}
          />
        );

      case 'inline':
        return (
          <Button
            type="text"
            size="small"
            icon={displayIcon}
            onClick={() => setModalOpen(true)}
            style={{ padding: '4px 8px' }}
          >
            {displayText}
          </Button>
        );

      case 'auto':
        // Auto trigger doesn't render a button, just manages the modal
        return null;

      case 'button':
      default:
        return tooltip ? (
          <Tooltip title={displayTooltip}>
            {triggerButton}
          </Tooltip>
        ) : (
          triggerButton
        );
    }
  };

  return (
    <>
      {renderTrigger()}
      
      <FeedbackModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleFeedbackSubmit}
        touchpoint={touchpoint}
        context={context}
        title={title}
        description={description}
      />
    </>
  );
};

export default FeedbackTrigger;