import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TravelModesPage } from './TravelModesPage';

// Mock components
jest.mock('@/components', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: any) => <h3 data-testid="card-title">{children}</h3>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
  Button: ({ children, onClick, disabled, variant }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant}>
      {children}
    </button>
  ),
  Input: ({ label, value, onChange, placeholder, type }: any) => (
    <div>
      {label && <label>{label}</label>}
      <input
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        type={type || 'text'}
        data-testid={`input-${label?.toLowerCase().replace(/\s+/g, '-')}`}
      />
    </div>
  ),
  Select: ({ label, value, onChange, children }: any) => (
    <div>
      {label && <label>{label}</label>}
      <select value={value} onChange={onChange} data-testid={`select-${label?.toLowerCase().replace(/\s+/g, '-')}`}>
        {children}
      </select>
    </div>
  ),
  Checkbox: ({ label, checked, onChange }: any) => (
    <div>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        data-testid={`checkbox-${label?.toLowerCase()}`}
      />
      <label>{label}</label>
    </div>
  ),
  Alert: ({ children, variant }: any) => (
    <div role="alert" data-variant={variant}>{children}</div>
  ),
  Spinner: () => <div data-testid="spinner">Loading...</div>
}));

// Mock hooks
jest.mock('@/hooks', () => ({
  useMapData: () => ({
    setIsochrones: jest.fn(),
    clearMap: jest.fn(),
    loadAnalysisResult: jest.fn()
  })
}));

// Mock API context
jest.mock('@/contexts', () => ({
  useAPI: () => ({
    createLocationAnalysis: jest.fn().mockResolvedValue({ job_id: 'test-job-123' }),
    getJobStatus: jest.fn().mockResolvedValue({ status: 'completed' }),
    getResults: jest.fn().mockResolvedValue({
      job_id: 'test-job-123',
      results: { accessibility_score: 0.85 }
    })
  })
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('TravelModesPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the page with basic elements', () => {
    render(<TravelModesPage />, { wrapper: createWrapper() });
    
    // Check for basic page structure
    expect(screen.getByText('Travel Modes Comparison')).toBeInTheDocument();
    expect(screen.getByText(/Compare accessibility/i)).toBeInTheDocument();
  });

  it('allows user to input location', async () => {
    const user = userEvent.setup();
    render(<TravelModesPage />, { wrapper: createWrapper() });
    
    const locationInput = screen.getByLabelText(/location/i);
    await user.clear(locationInput);
    await user.type(locationInput, 'New York, NY');
    
    expect(locationInput).toHaveValue('New York, NY');
  });

  it('has travel mode checkboxes', () => {
    render(<TravelModesPage />, { wrapper: createWrapper() });
    
    // Check for travel mode labels
    expect(screen.getByText('Walking')).toBeInTheDocument();
    expect(screen.getByText('Biking')).toBeInTheDocument();
    expect(screen.getByText('Driving')).toBeInTheDocument();
    expect(screen.getByText('Transit')).toBeInTheDocument();
  });

  it('shows analyze button', () => {
    render(<TravelModesPage />, { wrapper: createWrapper() });
    
    const analyzeButton = screen.getByRole('button', { name: /analyze/i });
    expect(analyzeButton).toBeInTheDocument();
  });

  it('allows travel time configuration', async () => {
    const user = userEvent.setup();
    render(<TravelModesPage />, { wrapper: createWrapper() });
    
    const travelTimeInput = screen.getByLabelText(/travel time/i);
    await user.clear(travelTimeInput);
    await user.type(travelTimeInput, '30');
    
    expect(travelTimeInput).toHaveValue('30');
  });
});