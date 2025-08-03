import { renderHook, act, waitFor } from '@testing-library/react';
import { useErrorHandler, useToastErrors } from './useErrorHandler';
import { APIError } from '../types/api';

describe('useErrorHandler', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('initial state', () => {
    it('should start with no errors', () => {
      const { result } = renderHook(() => useErrorHandler());

      expect(result.current.errors).toEqual([]);
      expect(result.current.latestError).toBeNull();
      expect(result.current.hasErrors()).toBe(false);
    });
  });

  describe('addError', () => {
    it('should add error with default severity', () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.addError('Test error message');
      });

      expect(result.current.errors).toHaveLength(1);
      expect(result.current.errors[0]).toMatchObject({
        message: 'Test error message',
        severity: 'error',
        duration: undefined,
      });
      expect(result.current.errors[0].id).toBeDefined();
      expect(result.current.errors[0].timestamp).toBeInstanceOf(Date);
    });

    it('should add error with custom properties', () => {
      const { result } = renderHook(() => useErrorHandler());
      const details = { code: 'ERR_001' };

      act(() => {
        result.current.addError('Custom error', 'warning', details, 3000);
      });

      expect(result.current.errors[0]).toMatchObject({
        message: 'Custom error',
        severity: 'warning',
        details,
        duration: 3000,
      });
    });

    it('should call onError callback', () => {
      const onError = jest.fn();
      const { result } = renderHook(() => useErrorHandler({ onError }));

      act(() => {
        result.current.addError('Test error');
      });

      expect(onError).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Test error',
          severity: 'error',
        })
      );
    });

    it('should limit number of errors', () => {
      const { result } = renderHook(() => useErrorHandler({ maxErrors: 3 }));

      act(() => {
        for (let i = 0; i < 5; i++) {
          result.current.addError(`Error ${i}`);
        }
      });

      expect(result.current.errors).toHaveLength(3);
      expect(result.current.errors[0].message).toBe('Error 2');
      expect(result.current.errors[2].message).toBe('Error 4');
    });
  });

  describe('removeError', () => {
    it('should remove error by ID', () => {
      const { result } = renderHook(() => useErrorHandler());
      let errorId: string;

      act(() => {
        errorId = result.current.addError('Error to remove');
      });

      expect(result.current.errors).toHaveLength(1);

      act(() => {
        result.current.removeError(errorId);
      });

      expect(result.current.errors).toHaveLength(0);
    });

    it('should not throw if ID not found', () => {
      const { result } = renderHook(() => useErrorHandler());

      expect(() => {
        act(() => {
          result.current.removeError('non-existent-id');
        });
      }).not.toThrow();
    });
  });

  describe('clearErrors', () => {
    it('should remove all errors', () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.addError('Error 1');
        result.current.addError('Error 2');
        result.current.addError('Error 3');
      });

      expect(result.current.errors).toHaveLength(3);

      act(() => {
        result.current.clearErrors();
      });

      expect(result.current.errors).toHaveLength(0);
    });
  });

  describe('handleAPIError', () => {
    it('should handle API error with appropriate severity', () => {
      const { result } = renderHook(() => useErrorHandler());
      const apiError: APIError = {
        error_code: 'RATE_LIMIT_EXCEEDED',
        message: 'Too many requests',
        timestamp: new Date().toISOString(),
      };

      act(() => {
        result.current.handleAPIError(apiError);
      });

      expect(result.current.errors[0]).toMatchObject({
        message: 'Too many requests. Please wait a moment and try again.',
        severity: 'warning',
        details: undefined,
      });
    });

    it('should handle unknown error codes', () => {
      const { result } = renderHook(() => useErrorHandler());
      const apiError: APIError = {
        error_code: 'UNKNOWN_ERROR',
        message: 'Something went wrong',
        timestamp: new Date().toISOString(),
      };

      act(() => {
        result.current.handleAPIError(apiError);
      });

      expect(result.current.errors[0].message).toBe('Something went wrong');
      expect(result.current.errors[0].severity).toBe('error');
    });
  });

  describe('handleError', () => {
    it('should handle Error objects', () => {
      const { result } = renderHook(() => useErrorHandler());
      const error = new Error('Test error');

      act(() => {
        result.current.handleError(error);
      });

      expect(result.current.errors[0].message).toBe('Test error');
    });

    it('should handle string errors', () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.handleError('String error');
      });

      expect(result.current.errors[0].message).toBe('String error');
    });
  });

  describe('convenience methods', () => {
    it('should show success message', () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.showSuccess('Operation completed');
      });

      expect(result.current.errors[0]).toMatchObject({
        message: 'Operation completed',
        severity: 'success',
        duration: 5000,
      });
    });

    it('should show info message', () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.showInfo('Information message', 3000);
      });

      expect(result.current.errors[0]).toMatchObject({
        message: 'Information message',
        severity: 'info',
        duration: 3000,
      });
    });

    it('should show warning message', () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.showWarning('Warning message');
      });

      expect(result.current.errors[0]).toMatchObject({
        message: 'Warning message',
        severity: 'warning',
        duration: 5000,
      });
    });
  });

  describe('auto-dismiss', () => {
    it('should auto-dismiss errors with duration', async () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.addError('Auto-dismiss error', 'info', undefined, 1000);
      });

      expect(result.current.errors).toHaveLength(1);

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(result.current.errors).toHaveLength(0);
      });
    });

    it('should not auto-dismiss errors without duration', () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.addError('Persistent error');
      });

      act(() => {
        jest.advanceTimersByTime(10000);
      });

      expect(result.current.errors).toHaveLength(1);
    });
  });

  describe('latestError', () => {
    it('should track the most recent error', () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.addError('First error');
      });

      expect(result.current.latestError?.message).toBe('First error');

      act(() => {
        result.current.addError('Second error');
      });

      expect(result.current.latestError?.message).toBe('Second error');

      act(() => {
        result.current.clearErrors();
      });

      expect(result.current.latestError).toBeNull();
    });
  });

  describe('hasErrors', () => {
    it('should check if any errors exist', () => {
      const { result } = renderHook(() => useErrorHandler());

      expect(result.current.hasErrors()).toBe(false);

      act(() => {
        result.current.addError('Error');
      });

      expect(result.current.hasErrors()).toBe(true);
    });

    it('should check for specific severity', () => {
      const { result } = renderHook(() => useErrorHandler());

      act(() => {
        result.current.showInfo('Info');
        result.current.showWarning('Warning');
      });

      expect(result.current.hasErrors('error')).toBe(false);
      expect(result.current.hasErrors('warning')).toBe(true);
      expect(result.current.hasErrors('info')).toBe(true);
    });
  });
});

describe('useToastErrors', () => {
  it('should manage toast messages', () => {
    const { result } = renderHook(() => useToastErrors());

    expect(result.current.toasts).toEqual([]);

    const toast = {
      id: 'toast-1',
      message: 'Toast message',
      severity: 'info' as const,
      timestamp: new Date(),
    };

    act(() => {
      result.current.showToast(toast);
    });

    expect(result.current.toasts).toEqual([toast]);

    act(() => {
      result.current.removeToast('toast-1');
    });

    expect(result.current.toasts).toEqual([]);
  });

  it('should clear all toasts', () => {
    const { result } = renderHook(() => useToastErrors());

    act(() => {
      result.current.showToast({
        id: '1',
        message: 'Toast 1',
        severity: 'info',
        timestamp: new Date(),
      });
      result.current.showToast({
        id: '2',
        message: 'Toast 2',
        severity: 'error',
        timestamp: new Date(),
      });
    });

    expect(result.current.toasts).toHaveLength(2);

    act(() => {
      result.current.clearToasts();
    });

    expect(result.current.toasts).toEqual([]);
  });

  it('should auto-remove toast with duration', async () => {
    jest.useFakeTimers();
    const { result } = renderHook(() => useToastErrors());

    act(() => {
      result.current.showToast({
        id: 'auto-remove',
        message: 'Auto-remove toast',
        severity: 'info',
        timestamp: new Date(),
        duration: 2000,
      });
    });

    expect(result.current.toasts).toHaveLength(1);

    act(() => {
      jest.advanceTimersByTime(2000);
    });

    await waitFor(() => {
      expect(result.current.toasts).toHaveLength(0);
    });

    jest.useRealTimers();
  });
});