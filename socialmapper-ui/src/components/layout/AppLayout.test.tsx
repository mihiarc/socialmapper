import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import AppLayout from './AppLayout';
import uiReducer from '@store/slices/uiSlice';

// Mock the Ant Design components that might cause issues in tests
vi.mock('antd', async () => {
  const actual = await vi.importActual('antd');
  return {
    ...actual,
    notification: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
      warning: vi.fn(),
    },
    message: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn(),
      warning: vi.fn(),
      loading: vi.fn(),
    },
  };
});

const createTestStore = () => {
  return configureStore({
    reducer: {
      ui: uiReducer,
    },
  });
};

const renderWithProviders = (component: React.ReactElement) => {
  const store = createTestStore();
  return render(
    <Provider store={store}>
      <BrowserRouter>{component}</BrowserRouter>
    </Provider>,
  );
};

describe('AppLayout', () => {
  it('renders without crashing', () => {
    renderWithProviders(<AppLayout />);
    expect(document.querySelector('.ant-layout')).toBeInTheDocument();
  });

  it('displays the application title', () => {
    renderWithProviders(<AppLayout />);
    const title = screen.getByText(/SocialMapper/i);
    expect(title).toBeInTheDocument();
  });

  it('renders navigation menu items', () => {
    renderWithProviders(<AppLayout />);
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/Analysis Wizard/i)).toBeInTheDocument();
    expect(screen.getByText(/Results/i)).toBeInTheDocument();
  });

  it('has a responsive layout structure', () => {
    const { container } = renderWithProviders(<AppLayout />);
    const layout = container.querySelector('.ant-layout');
    const sider = container.querySelector('.ant-layout-sider');
    const header = container.querySelector('.ant-layout-header');
    const content = container.querySelector('.ant-layout-content');

    expect(layout).toBeInTheDocument();
    expect(sider).toBeInTheDocument();
    expect(header).toBeInTheDocument();
    expect(content).toBeInTheDocument();
  });

  it('renders the outlet for child routes', () => {
    const { container } = renderWithProviders(<AppLayout />);
    const content = container.querySelector('.ant-layout-content');
    expect(content).toBeInTheDocument();
  });
});