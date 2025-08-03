import React from 'react';
import { render, screen } from '@testing-library/react';
import { Spinner } from './Spinner';

describe('Spinner', () => {
  it('renders spinner with default size', () => {
    render(<Spinner />);
    const spinner = screen.getByRole('status');
    
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('animate-spin');
    expect(spinner).toHaveClass('h-8', 'w-8'); // default medium size
  });

  it('renders with small size', () => {
    render(<Spinner size="sm" />);
    const spinner = screen.getByRole('status');
    
    expect(spinner).toHaveClass('h-4', 'w-4');
  });

  it('renders with large size', () => {
    render(<Spinner size="lg" />);
    const spinner = screen.getByRole('status');
    
    expect(spinner).toHaveClass('h-12', 'w-12');
  });

  it('applies custom className', () => {
    render(<Spinner className="custom-class" />);
    const spinner = screen.getByRole('status');
    
    expect(spinner).toHaveClass('custom-class');
    expect(spinner).toHaveClass('animate-spin'); // Should still have base class
  });

  it('has accessible attributes', () => {
    render(<Spinner />);
    const spinner = screen.getByRole('status');
    
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveAttribute('aria-label', 'Loading');
    expect(screen.getByText('Loading...')).toHaveClass('sr-only');
  });

  it('renders dots variant', () => {
    render(<Spinner variant="dots" />);
    const spinner = screen.getByRole('status');
    
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('flex', 'space-x-1.5');
    // The container has 3 dot divs, plus the sr-only span is a child element
    const dots = spinner.querySelectorAll('div');
    expect(dots.length).toBe(3); // 3 dots
  });

  it('renders pulse variant', () => {
    render(<Spinner variant="pulse" />);
    const spinner = screen.getByRole('status');
    
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('relative');
    expect(spinner.querySelector('.animate-ping')).toBeInTheDocument();
  });
});