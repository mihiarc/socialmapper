import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { HomePage } from './HomePage';

// Mock the components that HomePage uses
jest.mock('@/components', () => ({
  Card: ({ children, className }: any) => <div data-testid="card" className={className}>{children}</div>,
  CardHeader: ({ children }: any) => <div data-testid="card-header">{children}</div>,
  CardTitle: ({ children }: any) => <h3 data-testid="card-title">{children}</h3>,
  CardContent: ({ children }: any) => <div data-testid="card-content">{children}</div>,
  CardDescription: ({ children }: any) => <p data-testid="card-description">{children}</p>
}));

jest.mock('lucide-react', () => ({
  MapPin: () => <span data-testid="map-pin-icon">MapPin</span>,
  Upload: () => <span data-testid="upload-icon">Upload</span>,
  Compass: () => <span data-testid="compass-icon">Compass</span>,
  Map: () => <span data-testid="map-icon">Map</span>,
  Target: () => <span data-testid="target-icon">Target</span>,
  BarChart: () => <span data-testid="bar-chart-icon">BarChart</span>,
  ArrowRight: () => <span data-testid="arrow-right-icon">ArrowRight</span>,
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('HomePage', () => {
  it('renders the welcome message', () => {
    renderWithRouter(<HomePage />);
    
    expect(screen.getByText('Welcome to SocialMapper')).toBeInTheDocument();
    expect(screen.getByText(/Analyze accessibility to essential services/)).toBeInTheDocument();
  });

  it('renders all tutorial cards', () => {
    renderWithRouter(<HomePage />);
    
    // Check for all tutorial sections
    expect(screen.getByText('Getting Started')).toBeInTheDocument();
    expect(screen.getByText('Custom POIs')).toBeInTheDocument();
    expect(screen.getByText('Travel Modes')).toBeInTheDocument();
    expect(screen.getByText('ZCTA Analysis')).toBeInTheDocument();
    expect(screen.getByText('Address Geocoding')).toBeInTheDocument();
    expect(screen.getByText('Batch Analysis')).toBeInTheDocument();
  });

  it('renders tutorial links with correct hrefs', () => {
    renderWithRouter(<HomePage />);
    
    const links = screen.getAllByRole('link');
    
    // Check that links exist and have the expected hrefs
    expect(links.find(link => link.getAttribute('href') === '/getting-started')).toBeTruthy();
    expect(links.find(link => link.getAttribute('href') === '/custom-pois')).toBeTruthy();
    expect(links.find(link => link.getAttribute('href') === '/travel-modes')).toBeTruthy();
    expect(links.find(link => link.getAttribute('href') === '/zcta-analysis')).toBeTruthy();
    expect(links.find(link => link.getAttribute('href') === '/address-geocoding')).toBeTruthy();
    expect(links.find(link => link.getAttribute('href') === '/batch-analysis')).toBeTruthy();
  });

  it('renders icons for each tutorial section', () => {
    renderWithRouter(<HomePage />);
    
    expect(screen.getByTestId('map-pin-icon')).toBeInTheDocument();
    expect(screen.getByTestId('upload-icon')).toBeInTheDocument();
    expect(screen.getByTestId('compass-icon')).toBeInTheDocument();
    expect(screen.getByTestId('map-icon')).toBeInTheDocument();
    expect(screen.getByTestId('target-icon')).toBeInTheDocument();
    expect(screen.getByTestId('bar-chart-icon')).toBeInTheDocument();
  });

  it('applies proper styling classes', () => {
    renderWithRouter(<HomePage />);
    
    // Check for container classes
    const container = screen.getByText('Welcome to SocialMapper').closest('div');
    expect(container).toHaveClass('container');
    
    // Check for grid layout
    const tutorialGrid = screen.getAllByTestId('card')[0].parentElement;
    expect(tutorialGrid).toHaveClass('grid');
  });

  it('renders tutorial descriptions', () => {
    renderWithRouter(<HomePage />);
    
    expect(screen.getByText(/basic location analysis/)).toBeInTheDocument();
    expect(screen.getByText(/Upload your own points of interest/)).toBeInTheDocument();
    expect(screen.getByText(/Compare accessibility across different travel modes/)).toBeInTheDocument();
    expect(screen.getByText(/Analyze entire ZIP Code Tabulation Areas/)).toBeInTheDocument();
    expect(screen.getByText(/Convert addresses to coordinates/)).toBeInTheDocument();
    expect(screen.getByText(/Process multiple locations/)).toBeInTheDocument();
  });
});