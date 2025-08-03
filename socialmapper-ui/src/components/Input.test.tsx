import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Input } from './Input';

describe('Input', () => {
  it('renders basic input', () => {
    render(<Input />);
    const input = screen.getByRole('textbox');
    expect(input).toBeInTheDocument();
  });

  it('renders with label', () => {
    render(<Input label="Email Address" />);
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
  });

  it('renders with placeholder', () => {
    render(<Input placeholder="Enter your name" />);
    const input = screen.getByPlaceholderText('Enter your name');
    expect(input).toBeInTheDocument();
  });

  it('handles value changes', async () => {
    const user = userEvent.setup();
    const handleChange = jest.fn();
    
    render(<Input onChange={handleChange} />);
    const input = screen.getByRole('textbox');
    
    await user.type(input, 'test value');
    
    expect(handleChange).toHaveBeenCalledTimes(10); // Once for each character
    expect(input).toHaveValue('test value');
  });

  it('renders with error state', () => {
    render(<Input error="This field is required" />);
    expect(screen.getByText('This field is required')).toBeInTheDocument();
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-red-500');
  });

  it('renders as disabled', () => {
    render(<Input disabled label="Disabled Input" />);
    const input = screen.getByLabelText('Disabled Input');
    expect(input).toBeDisabled();
  });

  it('renders as required', () => {
    render(<Input required label="Required Field" />);
    const input = screen.getByLabelText('Required Field');
    expect(input).toBeRequired();
  });

  it('supports different input types', () => {
    const { rerender } = render(<Input type="email" />);
    let input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('type', 'email');

    rerender(<Input type="password" />);
    // Password inputs don't have textbox role
    const passwordInput = screen.getByDisplayValue('');
    expect(passwordInput).toHaveAttribute('type', 'password');

    rerender(<Input type="number" />);
    input = screen.getByRole('spinbutton');
    expect(input).toHaveAttribute('type', 'number');
  });

  it('applies custom className', () => {
    render(<Input className="custom-input" />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('custom-input');
  });

  it('forwards ref properly', () => {
    const ref = React.createRef<HTMLInputElement>();
    render(<Input ref={ref} />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });

  it('handles controlled input', () => {
    const ControlledInput = () => {
      const [value, setValue] = React.useState('initial');
      return (
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      );
    };

    render(<ControlledInput />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveValue('initial');
  });
});