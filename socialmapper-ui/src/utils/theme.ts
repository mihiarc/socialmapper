/**
 * Ant Design theme configuration
 * Customizes the design system for SocialMapper branding
 */
import type { ThemeConfig } from 'antd';

export const antdTheme: ThemeConfig = {
  token: {
    // Primary brand colors
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    
    // Layout
    borderRadius: 6,
    wireframe: false,
    
    // Typography
    fontSize: 14,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    
    // Spacing
    sizeUnit: 4,
    sizeStep: 4,
    
    // Component specific
    controlHeight: 32,
    controlOutlineWidth: 2,
  },
  components: {
    // Layout components
    Layout: {
      headerBg: '#ffffff',
      siderBg: '#ffffff',
      bodyBg: '#f5f5f5',
    },
    
    // Menu styling
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: '#e6f7ff',
      itemSelectedColor: '#1890ff',
      itemHoverBg: '#f0f0f0',
    },
    
    // Card styling
    Card: {
      borderRadiusLG: 8,
      boxShadowTertiary: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02)',
    },
    
    // Button customization
    Button: {
      borderRadius: 6,
      controlHeight: 40,
      paddingContentHorizontal: 16,
    },
    
    // Form components
    Input: {
      borderRadius: 6,
      controlHeight: 40,
    },
    
    Select: {
      borderRadius: 6,
      controlHeight: 40,
    },
    
    // Progress components
    Progress: {
      defaultColor: '#1890ff',
    },
    
    // Notification styling
    Notification: {
      borderRadiusOuter: 8,
    },
    
    // Modal styling
    Modal: {
      borderRadiusLG: 12,
    },
  },
  algorithm: [],
};