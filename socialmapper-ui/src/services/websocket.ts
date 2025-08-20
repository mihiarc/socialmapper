/**
 * WebSocket Service for real-time progress tracking
 * Provides reliable WebSocket connection with automatic reconnection
 */

import { store } from '@/store';
import { updateJobStatus, completeJob } from '@/store/slices/analysisSlice';
import { JobStatusEnum } from '@/types/api';

interface WebSocketMessage {
  type: 'progress' | 'stage_change' | 'completed' | 'failed' | 'log';
  job_id: string;
  data: {
    status?: JobStatusEnum;
    progress?: number;
    message?: string;
    stage?: string;
    estimated_completion?: string;
    error?: string;
    error_details?: string;
  };
  timestamp: string;
}

class WebSocketService {
  private sockets: Map<string, WebSocket> = new Map();
  private reconnectAttempts: Map<string, number> = new Map();
  private reconnectTimeouts: Map<string, NodeJS.Timeout> = new Map();
  private messageHandlers: Map<string, Set<(message: WebSocketMessage) => void>> = new Map();
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // Start with 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds

  /**
   * Connect to WebSocket for a specific job
   */
  connect(jobId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      // Don't create duplicate connections
      if (this.sockets.has(jobId) && this.sockets.get(jobId)?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = import.meta.env.VITE_API_URL?.replace(/^https?:\/\//, '') || window.location.host;
      const wsUrl = `${protocol}//${host}/ws/analysis/${jobId}/progress`;

      console.log(`Connecting to WebSocket: ${wsUrl}`);

      const socket = new WebSocket(wsUrl);
      this.sockets.set(jobId, socket);

      socket.onopen = () => {
        console.log(`WebSocket connected for job ${jobId}`);
        this.reconnectAttempts.set(jobId, 0);
        
        // Clear any pending reconnect timeout
        const timeout = this.reconnectTimeouts.get(jobId);
        if (timeout) {
          clearTimeout(timeout);
          this.reconnectTimeouts.delete(jobId);
        }
        
        resolve();
      };

      socket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(jobId, message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      socket.onerror = (error) => {
        console.error(`WebSocket error for job ${jobId}:`, error);
      };

      socket.onclose = (event) => {
        console.log(`WebSocket closed for job ${jobId}. Code: ${event.code}, Reason: ${event.reason}`);
        this.sockets.delete(jobId);

        // Attempt reconnection if not a normal closure
        if (event.code !== 1000 && event.code !== 1001) {
          this.scheduleReconnect(jobId);
        }
      };

      // Reject if connection doesn't open within 10 seconds
      setTimeout(() => {
        if (socket.readyState !== WebSocket.OPEN) {
          socket.close();
          reject(new Error(`WebSocket connection timeout for job ${jobId}`));
        }
      }, 10000);
    });
  }

  /**
   * Disconnect WebSocket for a specific job
   */
  disconnect(jobId: string): void {
    const socket = this.sockets.get(jobId);
    if (socket) {
      socket.close(1000, 'Client disconnecting');
      this.sockets.delete(jobId);
    }

    // Clear reconnect timeout if exists
    const timeout = this.reconnectTimeouts.get(jobId);
    if (timeout) {
      clearTimeout(timeout);
      this.reconnectTimeouts.delete(jobId);
    }

    // Clear handlers
    this.messageHandlers.delete(jobId);
    this.reconnectAttempts.delete(jobId);
  }

  /**
   * Disconnect all WebSocket connections
   */
  disconnectAll(): void {
    this.sockets.forEach((socket, jobId) => {
      this.disconnect(jobId);
    });
  }

  /**
   * Subscribe to messages for a specific job
   */
  subscribe(jobId: string, handler: (message: WebSocketMessage) => void): () => void {
    if (!this.messageHandlers.has(jobId)) {
      this.messageHandlers.set(jobId, new Set());
    }
    
    this.messageHandlers.get(jobId)?.add(handler);

    // Return unsubscribe function
    return () => {
      this.messageHandlers.get(jobId)?.delete(handler);
      if (this.messageHandlers.get(jobId)?.size === 0) {
        this.messageHandlers.delete(jobId);
      }
    };
  }

  /**
   * Send a message through the WebSocket
   */
  send(jobId: string, data: any): void {
    const socket = this.sockets.get(jobId);
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data));
    } else {
      console.warn(`WebSocket not connected for job ${jobId}`);
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(jobId: string, message: WebSocketMessage): void {
    console.log(`WebSocket message for job ${jobId}:`, message);

    // Update Redux store based on message type
    switch (message.type) {
      case 'progress':
      case 'stage_change':
        store.dispatch(updateJobStatus({
          id: jobId,
          status: message.data.status || JobStatusEnum.RUNNING,
          progress: message.data.progress || 0,
          message: message.data.message || ''
        }));
        break;

      case 'completed':
        store.dispatch(completeJob(jobId));
        // Auto-disconnect after completion
        setTimeout(() => this.disconnect(jobId), 1000);
        break;

      case 'failed':
        store.dispatch(updateJobStatus({
          id: jobId,
          status: JobStatusEnum.FAILED,
          progress: 0,
          message: message.data.error || 'Analysis failed'
        }));
        // Auto-disconnect after failure
        setTimeout(() => this.disconnect(jobId), 1000);
        break;

      case 'log':
        console.log(`[Job ${jobId}] ${message.data.message}`);
        break;
    }

    // Notify all subscribed handlers
    const handlers = this.messageHandlers.get(jobId);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(jobId: string): void {
    const attempts = this.reconnectAttempts.get(jobId) || 0;
    
    if (attempts >= this.maxReconnectAttempts) {
      console.error(`Max reconnection attempts reached for job ${jobId}`);
      store.dispatch(updateJobStatus({
        id: jobId,
        status: JobStatusEnum.FAILED,
        progress: 0,
        message: 'Lost connection to server'
      }));
      return;
    }

    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, attempts),
      this.maxReconnectDelay
    );

    console.log(`Scheduling reconnect for job ${jobId} in ${delay}ms (attempt ${attempts + 1}/${this.maxReconnectAttempts})`);

    const timeout = setTimeout(() => {
      this.reconnectAttempts.set(jobId, attempts + 1);
      this.connect(jobId).catch(error => {
        console.error(`Reconnection failed for job ${jobId}:`, error);
      });
    }, delay);

    this.reconnectTimeouts.set(jobId, timeout);
  }

  /**
   * Check if WebSocket is connected for a job
   */
  isConnected(jobId: string): boolean {
    const socket = this.sockets.get(jobId);
    return socket?.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection state for a job
   */
  getConnectionState(jobId: string): 'connecting' | 'connected' | 'disconnected' | 'error' {
    const socket = this.sockets.get(jobId);
    if (!socket) return 'disconnected';
    
    switch (socket.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'error';
    }
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();

// Export types
export type { WebSocketMessage };