import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Toast, ToastContainer } from './Toast';
import { ErrorMessage } from '../hooks/useErrorHandler';

describe('Toast', () => {
  const mockMessage: ErrorMessage = {
    id: 'test-1',
    message: 'Test error message',
    severity: 'error',
    timestamp: new Date(),
  };

  const mockOnDismiss = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('should render toast message', () => {
    render(<Toast message={mockMessage} onDismiss={mockOnDismiss} />);
    
    expect(screen.getByText('Test error message')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('should show correct icon for each severity', () => {
    const severities = {
      info: 'ℹ️',
      warning: '⚠️',
      error: '❌',
      success: '✅',
    };

    Object.entries(severities).forEach(([severity, icon]) => {
      const message = { ...mockMessage, severity: severity as any };
      const { rerender } = render(<Toast message={message} onDismiss={mockOnDismiss} />);
      
      expect(screen.getByText(icon)).toBeInTheDocument();
      rerender(<></>); // Clear for next iteration
    });
  });

  it('should apply correct styles for each severity', () => {
    const message = { ...mockMessage, severity: 'warning' as const };
    render(<Toast message={message} onDismiss={mockOnDismiss} />);
    
    const alert = screen.getByRole('alert');
    expect(alert).toHaveClass('bg-amber-50', 'text-amber-800', 'border-amber-200');
  });

  it('should call onDismiss when close button clicked', async () => {
    const user = userEvent.setup({ delay: null });
    render(<Toast message={mockMessage} onDismiss={mockOnDismiss} />);
    
    const closeButton = screen.getByLabelText('Dismiss');
    await user.click(closeButton);
    
    expect(mockOnDismiss).toHaveBeenCalledWith('test-1');
  });

  it('should display details when provided', () => {
    const messageWithDetails = {
      ...mockMessage,
      details: 'Additional error details',
    };
    
    render(<Toast message={messageWithDetails} onDismiss={mockOnDismiss} />);
    
    expect(screen.getByText('Additional error details')).toBeInTheDocument();
  });

  it('should stringify object details', () => {
    const messageWithObjectDetails = {
      ...mockMessage,
      details: { code: 'ERR_001', field: 'email' },
    };
    
    render(<Toast message={messageWithObjectDetails} onDismiss={mockOnDismiss} />);
    
    expect(screen.getByText(JSON.stringify(messageWithObjectDetails.details))).toBeInTheDocument();
  });

  it('should auto-dismiss after duration', () => {
    const messageWithDuration = {
      ...mockMessage,
      duration: 3000,
    };
    
    render(<Toast message={messageWithDuration} onDismiss={mockOnDismiss} />);
    
    expect(mockOnDismiss).not.toHaveBeenCalled();
    
    act(() => {
      jest.advanceTimersByTime(3000);
    });
    
    expect(mockOnDismiss).toHaveBeenCalledWith('test-1');
  });

  it('should not auto-dismiss without duration', () => {
    render(<Toast message={mockMessage} onDismiss={mockOnDismiss} />);
    
    act(() => {
      jest.advanceTimersByTime(10000);
    });
    
    expect(mockOnDismiss).not.toHaveBeenCalled();
  });

  it('should cleanup timer on unmount', () => {
    const messageWithDuration = {
      ...mockMessage,
      duration: 5000,
    };
    
    const { unmount } = render(<Toast message={messageWithDuration} onDismiss={mockOnDismiss} />);
    
    unmount();
    
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    
    expect(mockOnDismiss).not.toHaveBeenCalled();
  });
});

describe('ToastContainer', () => {
  const mockMessages: ErrorMessage[] = [
    {
      id: 'toast-1',
      message: 'First toast',
      severity: 'info',
      timestamp: new Date(),
    },
    {
      id: 'toast-2',
      message: 'Second toast',
      severity: 'error',
      timestamp: new Date(),
    },
  ];

  const mockOnDismiss = jest.fn();

  it('should render nothing when no messages', () => {
    const { container } = render(<ToastContainer messages={[]} onDismiss={mockOnDismiss} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render multiple toasts', () => {
    render(<ToastContainer messages={mockMessages} onDismiss={mockOnDismiss} />);
    
    expect(screen.getByText('First toast')).toBeInTheDocument();
    expect(screen.getByText('Second toast')).toBeInTheDocument();
    expect(screen.getAllByRole('alert')).toHaveLength(2);
  });

  it('should position container correctly', () => {
    render(<ToastContainer messages={mockMessages} onDismiss={mockOnDismiss} />);
    
    const container = screen.getAllByRole('alert')[0].parentElement;
    expect(container).toHaveClass('fixed', 'top-4', 'right-4', 'z-50');
  });

  it('should pass onDismiss to each toast', async () => {
    const user = userEvent.setup({ delay: null });
    render(<ToastContainer messages={mockMessages} onDismiss={mockOnDismiss} />);
    
    const closeButtons = screen.getAllByLabelText('Dismiss');
    await user.click(closeButtons[0]);
    
    expect(mockOnDismiss).toHaveBeenCalledWith('toast-1');
  });
});