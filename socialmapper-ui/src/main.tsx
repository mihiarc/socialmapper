import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';

import App from './App';
import { store } from '@store/index';
import { antdTheme } from '@utils/theme';
import { performanceMonitor } from '@utils/performance';
import './styles/globals.css';

// Initialize performance monitoring
if (typeof window !== 'undefined') {
  // Start performance monitoring
  performanceMonitor.recordFeatureUsage('app-start');
  
  // Log initial page load
  console.log('SocialMapper UI starting with performance monitoring enabled');
}

// App entry point with all necessary providers
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Provider store={store}>
        <ConfigProvider theme={antdTheme}>
          <App />
        </ConfigProvider>
      </Provider>
    </BrowserRouter>
  </React.StrictMode>,
);