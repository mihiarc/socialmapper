import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from 'react-query';

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

// React Query configuration for API caching and synchronization
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
});

// App entry point with all necessary providers
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          <ConfigProvider theme={antdTheme}>
            <App />
          </ConfigProvider>
        </QueryClientProvider>
      </Provider>
    </BrowserRouter>
  </React.StrictMode>,
);