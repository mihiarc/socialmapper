import React from 'react';
import { render, screen } from '@testing-library/react';
import { Card } from './Card';

describe('Card', () => {
  it('renders with children', () => {
    render(
      <Card>
        <h2>Card Title</h2>
        <p>Card content</p>
      </Card>
    );
    
    expect(screen.getByText('Card Title')).toBeInTheDocument();
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies default styling', () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstChild;
    
    expect(card).toHaveClass('bg-white');
    expect(card).toHaveClass('rounded-lg');
    expect(card).toHaveClass('shadow');
  });

  it('applies custom className', () => {
    const { container } = render(
      <Card className="custom-card-class">Content</Card>
    );
    const card = container.firstChild;
    
    expect(card).toHaveClass('custom-card-class');
    // Should still have base classes
    expect(card).toHaveClass('bg-white');
  });

  it('renders complex nested content', () => {
    render(
      <Card>
        <header>
          <h3>Header</h3>
        </header>
        <div>
          <button>Action</button>
        </div>
      </Card>
    );
    
    expect(screen.getByText('Header')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
  });

  it('maintains semantic HTML structure', () => {
    const { container } = render(
      <Card>
        <article>Article content</article>
      </Card>
    );
    
    expect(container.querySelector('article')).toBeInTheDocument();
    expect(screen.getByText('Article content')).toBeInTheDocument();
  });
});