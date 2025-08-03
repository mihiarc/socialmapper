import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SettingsPage } from './SettingsPage';

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock as any;

// Mock components
jest.mock('@/components', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: any) => <h3 data-testid="card-title">{children}</h3>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
  Input: ({ label, value, onChange, placeholder, type, error }: any) => (
    <div>
      {label && <label>{label}</label>}
      <input
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        type={type || 'text'}
        aria-invalid={!!error}
      />
      {error && <span role="alert">{error}</span>}
    </div>
  ),
  Button: ({ children, onClick, variant, disabled }: any) => (
    <button 
      onClick={onClick} 
      data-variant={variant}
      disabled={disabled}
    >
      {children}
    </button>
  ),
  Alert: ({ children, variant }: any) => (
    <div role="alert" data-variant={variant}>{children}</div>
  ),
  Spinner: () => <div data-testid="spinner">Loading...</div>
}));

// Mock hooks
jest.mock('@/hooks', () => ({
  useToast: () => ({
    toast: jest.fn()
  })
}));

describe('SettingsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  it('renders the settings page with all sections', () => {
    render(<SettingsPage />);
    
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Configure your SocialMapper API connection')).toBeInTheDocument();
    expect(screen.getByText('API Configuration')).toBeInTheDocument();
  });

  it('loads saved settings from localStorage', () => {
    const savedSettings = {
      apiUrl: 'https://custom.api.com',
      apiKey: 'test-key-123'
    };
    localStorageMock.getItem.mockReturnValue(JSON.stringify(savedSettings));
    
    render(<SettingsPage />);
    
    const urlInput = screen.getByDisplayValue('https://custom.api.com');
    const keyInput = screen.getByDisplayValue('test-key-123');
    
    expect(urlInput).toBeInTheDocument();
    expect(keyInput).toBeInTheDocument();
  });

  it('validates API URL format', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    
    const urlInput = screen.getByPlaceholderText('http://localhost:8000');
    const saveButton = screen.getByText('Save Settings');
    
    // Test invalid URL
    await user.clear(urlInput);
    await user.type(urlInput, 'not-a-url');
    await user.click(saveButton);
    
    expect(screen.getByText('Please enter a valid URL')).toBeInTheDocument();
  });

  it('saves settings to localStorage', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    
    const urlInput = screen.getByPlaceholderText('http://localhost:8000');
    const keyInput = screen.getByPlaceholderText('Enter your API key (optional)');
    const saveButton = screen.getByText('Save Settings');
    
    await user.clear(urlInput);
    await user.type(urlInput, 'http://new-api.com');
    await user.type(keyInput, 'new-key-456');
    await user.click(saveButton);
    
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'socialmapper_settings',
      JSON.stringify({
        apiUrl: 'http://new-api.com',
        apiKey: 'new-key-456'
      })
    );
    
    // Check for success message
    await waitFor(() => {
      expect(screen.getByText(/Settings saved successfully/)).toBeInTheDocument();
    });
  });

  it('tests API connection', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    
    const testButton = screen.getByText('Test Connection');
    
    // Mock successful API test
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'healthy' })
      })
    ) as jest.Mock;
    
    await user.click(testButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Connection successful/)).toBeInTheDocument();
    });
  });

  it('handles API connection test failure', async () => {
    const user = userEvent.setup();
    render(<SettingsPage />);
    
    const testButton = screen.getByText('Test Connection');
    
    // Mock failed API test
    global.fetch = jest.fn(() =>
      Promise.reject(new Error('Network error'))
    ) as jest.Mock;
    
    await user.click(testButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Connection failed/)).toBeInTheDocument();
    });
  });

  it('resets settings to defaults', async () => {
    const user = userEvent.setup();
    
    // Set some custom values first
    localStorageMock.getItem.mockReturnValue(JSON.stringify({
      apiUrl: 'https://custom.api.com',
      apiKey: 'test-key'
    }));
    
    render(<SettingsPage />);
    
    const resetButton = screen.getByText('Reset to Defaults');
    await user.click(resetButton);
    
    // Should show default URL
    expect(screen.getByDisplayValue('http://localhost:8000')).toBeInTheDocument();
    
    // API key should be empty
    const keyInput = screen.getByPlaceholderText('Enter your API key (optional)');
    expect(keyInput).toHaveValue('');
    
    // LocalStorage should be cleared
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('socialmapper_settings');
  });

  it('disables save button when URL is invalid', () => {
    render(<SettingsPage />);
    
    const urlInput = screen.getByPlaceholderText('http://localhost:8000');
    const saveButton = screen.getByText('Save Settings');
    
    fireEvent.change(urlInput, { target: { value: '' } });
    
    expect(saveButton).toBeDisabled();
  });
});