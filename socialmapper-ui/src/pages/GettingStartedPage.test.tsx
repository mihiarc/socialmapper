import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GettingStartedPage } from './GettingStartedPage';
import { APIProvider } from '@/contexts';
import { TravelMode, JobStatusEnum } from '@/types';

// Mock the API
const mockAPI = {
  getPOITypes: jest.fn(),
  getCensusVariables: jest.fn(),
  createLocationAnalysis: jest.fn(),
  pollJobStatus: jest.fn(),
  exportResults: jest.fn(),
  downloadExport: jest.fn(),
};

jest.mock('@/contexts', () => ({
  ...jest.requireActual('@/contexts'),
  useAPI: () => mockAPI,
}));

describe('GettingStartedPage', () => {
  let queryClient: QueryClient;

  const renderPage = () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    return render(
      <QueryClientProvider client={queryClient}>
        <APIProvider>
          <GettingStartedPage />
        </APIProvider>
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default mock responses
    mockAPI.getPOITypes.mockResolvedValue({
      poi_types: [
        { type: 'amenity', name: 'library', description: 'Libraries' },
        { type: 'amenity', name: 'school', description: 'Schools' },
      ],
      total_count: 2,
      categories: ['Education'],
    });

    mockAPI.getCensusVariables.mockResolvedValue({
      variables: [
        { code: 'B01003_001E', name: 'Total Population', group: 'Demographics' },
        { code: 'B19013_001E', name: 'Median Income', group: 'Income' },
      ],
      total_count: 2,
      categories: ['Demographics', 'Income'],
    });
  });

  it('should render page title and description', () => {
    renderPage();

    expect(screen.getByText('Getting Started')).toBeInTheDocument();
    expect(screen.getByText(/Analyze community accessibility/)).toBeInTheDocument();
  });

  it('should load POI types and census variables', async () => {
    renderPage();

    await waitFor(() => {
      expect(mockAPI.getPOITypes).toHaveBeenCalledWith({ limit: 50 });
      expect(mockAPI.getCensusVariables).toHaveBeenCalledWith({ limit: 20 });
    });
  });

  it('should render form fields', () => {
    renderPage();

    expect(screen.getByPlaceholderText('e.g., Portland, OR')).toBeInTheDocument();
    expect(screen.getByLabelText('Travel Mode')).toBeInTheDocument();
    expect(screen.getByLabelText('Travel Time (minutes)')).toBeInTheDocument();
  });

  it('should have default values', () => {
    renderPage();

    const travelModeSelect = screen.getByLabelText('Travel Mode') as HTMLSelectElement;
    const travelTimeInput = screen.getByLabelText('Travel Time (minutes)') as HTMLInputElement;

    expect(travelModeSelect.value).toBe(TravelMode.Walk);
    expect(travelTimeInput.value).toBe('15');
  });

  it('should submit analysis request', async () => {
    const user = userEvent.setup();
    const mockJobId = 'test-job-123';
    const mockResult = {
      job_id: mockJobId,
      status: JobStatusEnum.Completed,
      poi_count: 5,
      demographics: { B01003_001E: 50000 },
    };

    mockAPI.createLocationAnalysis.mockResolvedValue({
      job_id: mockJobId,
      status: JobStatusEnum.Pending,
    });
    mockAPI.pollJobStatus.mockResolvedValue(mockResult);

    renderPage();

    // Fill in the form
    const locationInput = screen.getByPlaceholderText('e.g., Portland, OR');
    await user.type(locationInput, 'Portland, OR');

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /analyze/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockAPI.createLocationAnalysis).toHaveBeenCalledWith({
        location: 'Portland, OR',
        travel_mode: TravelMode.Walk,
        travel_time_minutes: 15,
        poi_types: ['amenity:library'],
        census_variables: ['B01003_001E'],
      });
    });

    expect(mockAPI.pollJobStatus).toHaveBeenCalledWith(
      mockJobId,
      expect.any(Function)
    );
  });

  it('should update travel mode', async () => {
    const user = userEvent.setup();
    renderPage();

    const travelModeSelect = screen.getByLabelText('Travel Mode');
    await user.selectOptions(travelModeSelect, TravelMode.Bike);

    expect(travelModeSelect).toHaveValue(TravelMode.Bike);
  });

  it('should update travel time', async () => {
    const user = userEvent.setup();
    renderPage();

    const travelTimeInput = screen.getByLabelText('Travel Time (minutes)');
    await user.clear(travelTimeInput);
    await user.type(travelTimeInput, '30');

    expect(travelTimeInput).toHaveValue('30');
  });

  it('should validate travel time range', () => {
    renderPage();

    const travelTimeInput = screen.getByLabelText('Travel Time (minutes)') as HTMLInputElement;
    expect(travelTimeInput.min).toBe('5');
    expect(travelTimeInput.max).toBe('60');
  });

  it('should show loading state during analysis', async () => {
    const user = userEvent.setup();
    
    // Create a promise that we can control
    let resolveAnalysis: any;
    const analysisPromise = new Promise((resolve) => {
      resolveAnalysis = resolve;
    });

    mockAPI.createLocationAnalysis.mockReturnValue(analysisPromise);

    renderPage();

    // Fill and submit form
    const locationInput = screen.getByPlaceholderText('e.g., Portland, OR');
    await user.type(locationInput, 'Portland, OR');

    const submitButton = screen.getByRole('button', { name: /analyze/i });
    await user.click(submitButton);

    // Should show loading state
    expect(screen.getByText(/analyzing/i)).toBeInTheDocument();

    // Resolve the promise
    resolveAnalysis({
      job_id: 'test-job',
      status: JobStatusEnum.Pending,
    });

    await waitFor(() => {
      expect(mockAPI.pollJobStatus).toHaveBeenCalled();
    });
  });

  it('should handle analysis errors', async () => {
    const user = userEvent.setup();
    const errorMessage = 'Network error';

    mockAPI.createLocationAnalysis.mockRejectedValue(new Error(errorMessage));

    renderPage();

    // Fill and submit form
    const locationInput = screen.getByPlaceholderText('e.g., Portland, OR');
    await user.type(locationInput, 'Portland, OR');

    const submitButton = screen.getByRole('button', { name: /analyze/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(new RegExp(errorMessage))).toBeInTheDocument();
    });
  });

  it('should display results after successful analysis', async () => {
    const user = userEvent.setup();
    const mockResult = {
      job_id: 'test-job',
      status: JobStatusEnum.Completed,
      poi_count: 5,
      demographics: { 
        B01003_001E: 50000,
        B19013_001E: 75000,
      },
      processing_time_seconds: 12.5,
    };

    mockAPI.createLocationAnalysis.mockResolvedValue({
      job_id: 'test-job',
      status: JobStatusEnum.Pending,
    });
    mockAPI.pollJobStatus.mockResolvedValue(mockResult);

    renderPage();

    // Submit analysis
    const locationInput = screen.getByPlaceholderText('e.g., Portland, OR');
    await user.type(locationInput, 'Portland, OR');
    
    const submitButton = screen.getByRole('button', { name: /analyze/i });
    await user.click(submitButton);

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText(/5 POIs found/i)).toBeInTheDocument();
      expect(screen.getByText(/50,000/)).toBeInTheDocument(); // Population
      expect(screen.getByText(/75,000/)).toBeInTheDocument(); // Income
    });
  });

  it('should allow exporting results', async () => {
    const user = userEvent.setup();
    const mockBlob = new Blob(['test data'], { type: 'text/csv' });

    mockAPI.createLocationAnalysis.mockResolvedValue({
      job_id: 'test-job',
      status: JobStatusEnum.Pending,
    });
    mockAPI.pollJobStatus.mockResolvedValue({
      job_id: 'test-job',
      status: JobStatusEnum.Completed,
      poi_count: 5,
    });
    mockAPI.downloadExport.mockResolvedValue(undefined);

    renderPage();

    // Submit analysis
    const locationInput = screen.getByPlaceholderText('e.g., Portland, OR');
    await user.type(locationInput, 'Portland, OR');
    
    const submitButton = screen.getByRole('button', { name: /analyze/i });
    await user.click(submitButton);

    // Wait for results and export button
    await waitFor(() => {
      expect(screen.getByText(/export/i)).toBeInTheDocument();
    });

    // Click export
    const exportButton = screen.getByRole('button', { name: /export.*csv/i });
    await user.click(exportButton);

    expect(mockAPI.downloadExport).toHaveBeenCalledWith(
      'test-job',
      ExportFormat.CSV,
      expect.any(String)
    );
  });
});