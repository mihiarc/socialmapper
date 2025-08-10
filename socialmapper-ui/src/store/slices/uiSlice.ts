/**
 * UI slice for managing global UI state
 * Handles loading states, notifications, modals, and user preferences
 */
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface NotificationData {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  message: string;
  duration?: number;
  timestamp: string;
}

export interface MapState {
  center: [number, number]; // [lng, lat]
  zoom: number;
  pitch: number;
  bearing: number;
}

interface UIState {
  // Loading states
  isLoading: boolean;
  loadingMessage?: string;
  
  // Notifications
  notifications: NotificationData[];
  
  // Modals
  activeModal?: string;
  modalData?: any;
  
  // Sidebar and layout
  sidebarCollapsed: boolean;
  
  // Map state
  mapState: MapState;
  
  // User preferences
  theme: 'light' | 'dark';
  units: 'metric' | 'imperial';
  mapStyle: string;
  
  // Progress tracking
  showProgressPanel: boolean;
}

const initialState: UIState = {
  isLoading: false,
  notifications: [],
  sidebarCollapsed: false,
  mapState: {
    center: [-98.5795, 39.8283], // Geographic center of US
    zoom: 4,
    pitch: 0,
    bearing: 0,
  },
  theme: 'light',
  units: 'metric',
  mapStyle: 'mapbox://styles/mapbox/light-v11',
  showProgressPanel: false,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Loading states
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
      if (!action.payload) {
        state.loadingMessage = undefined;
      }
    },

    setLoadingMessage: (state, action: PayloadAction<string>) => {
      state.isLoading = true;
      state.loadingMessage = action.payload;
    },

    // Notifications
    addNotification: (state, action: PayloadAction<Omit<NotificationData, 'id' | 'timestamp'>>) => {
      const notification: NotificationData = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
      };
      state.notifications.push(notification);
    },

    removeNotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },

    clearAllNotifications: (state) => {
      state.notifications = [];
    },

    // Modals
    openModal: (state, action: PayloadAction<{ modal: string; data?: any }>) => {
      state.activeModal = action.payload.modal;
      state.modalData = action.payload.data;
    },

    closeModal: (state) => {
      state.activeModal = undefined;
      state.modalData = undefined;
    },

    // Layout
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },

    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload;
    },

    // Map state
    updateMapState: (state, action: PayloadAction<Partial<MapState>>) => {
      state.mapState = { ...state.mapState, ...action.payload };
    },

    setMapCenter: (state, action: PayloadAction<[number, number]>) => {
      state.mapState.center = action.payload;
    },

    setMapZoom: (state, action: PayloadAction<number>) => {
      state.mapState.zoom = action.payload;
    },

    // User preferences
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
      state.mapStyle = action.payload === 'dark' 
        ? 'mapbox://styles/mapbox/dark-v11' 
        : 'mapbox://styles/mapbox/light-v11';
    },

    setUnits: (state, action: PayloadAction<'metric' | 'imperial'>) => {
      state.units = action.payload;
    },

    setMapStyle: (state, action: PayloadAction<string>) => {
      state.mapStyle = action.payload;
    },

    // Progress panel
    showProgressPanel: (state) => {
      state.showProgressPanel = true;
    },

    hideProgressPanel: (state) => {
      state.showProgressPanel = false;
    },

    // Utility actions
    showSuccessNotification: (state, action: PayloadAction<{ title: string; message: string }>) => {
      const notification: NotificationData = {
        ...action.payload,
        id: Date.now().toString(),
        type: 'success',
        timestamp: new Date().toISOString(),
        duration: 4000,
      };
      state.notifications.push(notification);
    },

    showErrorNotification: (state, action: PayloadAction<{ title: string; message: string }>) => {
      const notification: NotificationData = {
        ...action.payload,
        id: Date.now().toString(),
        type: 'error',
        timestamp: new Date().toISOString(),
        duration: 6000,
      };
      state.notifications.push(notification);
    },

    showInfoNotification: (state, action: PayloadAction<{ title: string; message: string }>) => {
      const notification: NotificationData = {
        ...action.payload,
        id: Date.now().toString(),
        type: 'info',
        timestamp: new Date().toISOString(),
        duration: 4000,
      };
      state.notifications.push(notification);
    },
  },
});

export const {
  setLoading,
  setLoadingMessage,
  addNotification,
  removeNotification,
  clearAllNotifications,
  openModal,
  closeModal,
  toggleSidebar,
  setSidebarCollapsed,
  updateMapState,
  setMapCenter,
  setMapZoom,
  setTheme,
  setUnits,
  setMapStyle,
  showProgressPanel,
  hideProgressPanel,
  showSuccessNotification,
  showErrorNotification,
  showInfoNotification,
} = uiSlice.actions;

export default uiSlice.reducer;