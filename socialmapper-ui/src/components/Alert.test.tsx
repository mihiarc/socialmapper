import React from 'react';
import { render, screen } from '@testing-library/react';
import { Alert } from './Alert';

describe('Alert', () => {
  it('renders with default variant (info)', () => {
    render(<Alert>Info message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveClass('bg-blue-100', 'text-blue-800');
    expect(screen.getByText('Info message')).toBeInTheDocument();
  });

  it('renders success variant', () => {
    render(<Alert variant="success">Success message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('bg-green-100', 'text-green-800');
  });

  it('renders warning variant', () => {
    render(<Alert variant="warning">Warning message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('bg-yellow-100', 'text-yellow-800');
  });

  it('renders error variant', () => {
    render(<Alert variant="error">Error message</Alert>);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('bg-red-100', 'text-red-800');
  });

  it('applies custom className', () => {
    render(
      <Alert className="custom-class">
        Custom styled alert
      </Alert>
    );
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('custom-class');
  });

  it('renders children content', () => {
    render(
      <Alert>
        <strong>Important:</strong> <span>Complex content</span>
      </Alert>
    );
    expect(screen.getByText('Important:')).toBeInTheDocument();
    expect(screen.getByText('Complex content')).toBeInTheDocument();
  });
});