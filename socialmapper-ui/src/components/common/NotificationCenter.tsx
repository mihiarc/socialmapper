/**
 * Global notification center component
 * Displays toast notifications for user feedback
 */
import React, { useEffect } from 'react';
import { notification } from 'antd';
import { useSelector, useDispatch } from 'react-redux';
import {
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';

import type { RootState } from '@store/index';
import { removeNotification } from '@store/slices/uiSlice';

/**
 * Centralized notification management
 * Automatically displays notifications from the Redux store
 */
const NotificationCenter: React.FC = () => {
  const dispatch = useDispatch();
  const { notifications } = useSelector((state: RootState) => state.ui);

  // Icon mapping for notification types
  const iconMap = {
    success: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    error: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
    warning: <ExclamationCircleOutlined style={{ color: '#faad14' }} />,
    info: <InfoCircleOutlined style={{ color: '#1890ff' }} />,
  };

  useEffect(() => {
    // Display new notifications
    notifications.forEach((notif) => {
      notification[notif.type]({
        key: notif.id,
        message: notif.title,
        description: notif.message,
        icon: iconMap[notif.type],
        duration: notif.duration || 4,
        onClose: () => {
          dispatch(removeNotification(notif.id));
        },
      });
    });

    // Clean up displayed notifications from store
    if (notifications.length > 0) {
      const timer = setTimeout(() => {
        notifications.forEach((notif) => {
          dispatch(removeNotification(notif.id));
        });
      }, 100);

      return () => clearTimeout(timer);
    }
    
    return undefined;
  }, [notifications, dispatch]);

  return null; // This component doesn't render anything directly
};

export default NotificationCenter;