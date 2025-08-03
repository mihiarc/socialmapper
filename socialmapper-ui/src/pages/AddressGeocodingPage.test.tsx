import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AddressGeocodingPage } from './AddressGeocodingPage';

// Mock components
jest.mock('@/components/Card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>
}));

jest.mock('@/components/Button', () => ({
  Button: ({ children, onClick, disabled, variant }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant}>
      {children}
    </button>
  )
}));

jest.mock('@/components/TextArea', () => ({
  TextArea: ({ value, onChange, placeholder, rows }: any) => (
    <textarea
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      rows={rows}
      data-testid="address-textarea"
    />
  )
}));

jest.mock('@/components/Alert', () => ({
  Alert: ({ children, variant }: any) => (
    <div role="alert" data-variant={variant}>{children}</div>
  )
}));

jest.mock('@/components/Spinner', () => ({
  Spinner: () => <div data-testid="spinner">Loading...</div>
}));

// Mock the API client
jest.mock('@/services/apiClient', () => ({
  apiClient: {
    geocoding: {
      geocodeAddresses: jest.fn()
    }
  }
}));

import { apiClient } from '@/services/apiClient';

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

describe('AddressGeocodingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the page with initial elements', () => {
    render(<AddressGeocodingPage />, { wrapper: createWrapper() });
    
    expect(screen.getByText('Address Geocoding')).toBeInTheDocument();
    expect(screen.getByText(/Convert addresses to geographic coordinates/)).toBeInTheDocument();
    expect(screen.getByTestId('address-textarea')).toBeInTheDocument();
    expect(screen.getByText('Geocode Addresses')).toBeInTheDocument();
  });

  it('shows instructions for address format', () => {
    render(<AddressGeocodingPage />, { wrapper: createWrapper() });
    
    expect(screen.getByText(/Enter addresses, one per line/)).toBeInTheDocument();
  });

  it('enables geocode button when addresses are entered', async () => {
    const user = userEvent.setup();
    render(<AddressGeocodingPage />, { wrapper: createWrapper() });
    
    const textarea = screen.getByTestId('address-textarea');
    const geocodeButton = screen.getByText('Geocode Addresses');
    
    expect(geocodeButton).toBeDisabled();
    
    await user.type(textarea, '123 Main St, Portland, OR');
    
    expect(geocodeButton).not.toBeDisabled();
  });

  it('geocodes addresses successfully', async () => {
    const user = userEvent.setup();
    const mockResults = [
      {
        address: '123 Main St, Portland, OR',
        latitude: 45.5152,
        longitude: -122.6784,
        formatted_address: '123 Main Street, Portland, OR 97201',
        confidence: 0.95
      }
    ];
    
    (apiClient.geocoding.geocodeAddresses as jest.Mock).mockResolvedValue(mockResults);
    
    render(<AddressGeocodingPage />, { wrapper: createWrapper() });
    
    const textarea = screen.getByTestId('address-textarea');
    const geocodeButton = screen.getByText('Geocode Addresses');
    
    await user.type(textarea, '123 Main St, Portland, OR');
    await user.click(geocodeButton);
    
    await waitFor(() => {
      expect(screen.getByText('Geocoding Results')).toBeInTheDocument();
      expect(screen.getByText('123 Main Street, Portland, OR 97201')).toBeInTheDocument();
      expect(screen.getByText(/45.5152/)).toBeInTheDocument();
      expect(screen.getByText(/-122.6784/)).toBeInTheDocument();
    });
  });

  it('handles geocoding errors', async () => {
    const user = userEvent.setup();
    (apiClient.geocoding.geocodeAddresses as jest.Mock).mockRejectedValue(
      new Error('Geocoding service unavailable')
    );
    
    render(<AddressGeocodingPage />, { wrapper: createWrapper() });
    
    const textarea = screen.getByTestId('address-textarea');
    const geocodeButton = screen.getByText('Geocode Addresses');
    
    await user.type(textarea, 'Invalid Address');
    await user.click(geocodeButton);
    
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Failed to geocode addresses/);
    });
  });

  it('shows loading state during geocoding', async () => {
    const user = userEvent.setup();
    
    // Create a promise that we can control
    let resolveGeocoding: any;
    const geocodingPromise = new Promise((resolve) => {
      resolveGeocoding = resolve;
    });
    
    (apiClient.geocoding.geocodeAddresses as jest.Mock).mockReturnValue(geocodingPromise);
    
    render(<AddressGeocodingPage />, { wrapper: createWrapper() });
    
    const textarea = screen.getByTestId('address-textarea');
    const geocodeButton = screen.getByText('Geocode Addresses');
    
    await user.type(textarea, '123 Main St');
    await user.click(geocodeButton);
    
    // Should show loading state
    expect(screen.getByTestId('spinner')).toBeInTheDocument();
    expect(geocodeButton).toBeDisabled();
    
    // Resolve the promise
    resolveGeocoding([]);
    
    await waitFor(() => {
      expect(screen.queryByTestId('spinner')).not.toBeInTheDocument();
    });
  });

  it('allows copying results to clipboard', async () => {
    const user = userEvent.setup();
    const mockResults = [
      {
        address: '123 Main St',
        latitude: 45.5,
        longitude: -122.6,
        formatted_address: '123 Main St',
        confidence: 0.9
      }
    ];
    
    (apiClient.geocoding.geocodeAddresses as jest.Mock).mockResolvedValue(mockResults);
    
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockResolvedValue(undefined)
      }
    });
    
    render(<AddressGeocodingPage />, { wrapper: createWrapper() });
    
    const textarea = screen.getByTestId('address-textarea');
    await user.type(textarea, '123 Main St');
    await user.click(screen.getByText('Geocode Addresses'));
    
    await waitFor(() => {
      expect(screen.getByText('Copy Results')).toBeInTheDocument();
    });
    
    await user.click(screen.getByText('Copy Results'));
    
    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });

  it('handles multiple addresses', async () => {
    const user = userEvent.setup();
    const mockResults = [
      {
        address: '123 Main St',
        latitude: 45.5,
        longitude: -122.6,
        formatted_address: '123 Main St',
        confidence: 0.9
      },
      {
        address: '456 Oak Ave',
        latitude: 45.6,
        longitude: -122.7,
        formatted_address: '456 Oak Avenue',
        confidence: 0.85
      }
    ];
    
    (apiClient.geocoding.geocodeAddresses as jest.Mock).mockResolvedValue(mockResults);
    
    render(<AddressGeocodingPage />, { wrapper: createWrapper() });
    
    const textarea = screen.getByTestId('address-textarea');
    await user.type(textarea, '123 Main St\n456 Oak Ave');
    await user.click(screen.getByText('Geocode Addresses'));
    
    await waitFor(() => {
      expect(screen.getByText('123 Main St')).toBeInTheDocument();
      expect(screen.getByText('456 Oak Avenue')).toBeInTheDocument();
    });
  });
});