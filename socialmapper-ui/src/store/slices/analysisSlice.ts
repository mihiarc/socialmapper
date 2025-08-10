/**
 * Analysis slice for managing analysis configuration state
 * Handles the analysis wizard form state and job tracking
 */
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type {
  GeographicLevel,
  JobStatusEnum,
  LocationAnalysisRequest,
  TravelMode,
} from '@types/api';

export interface AnalysisConfiguration {
  // Location information
  location: string;
  poi_type: string;
  poi_name: string;
  
  // Analysis parameters
  travel_time: number;
  travel_mode: TravelMode;
  geographic_level: GeographicLevel;
  census_variables: string[];
  include_isochrones: boolean;
  include_demographics: boolean;
}

export interface ActiveJob {
  id: string;
  status: JobStatusEnum;
  progress: number;
  message?: string;
  created_at: string;
  started_at?: string;
  updated_at: string;
  estimated_completion?: string;
}

interface AnalysisState {
  // Current configuration being built in the wizard
  currentConfig: Partial<AnalysisConfiguration>;
  
  // Validation state
  validationErrors: Record<string, string>;
  
  // Active jobs tracking
  activeJobs: ActiveJob[];
  
  // Recently completed analyses
  recentAnalyses: string[]; // job IDs
  
  // Wizard state
  currentStep: number;
  isSubmitting: boolean;
  
  // Demo scenarios
  selectedDemoScenario?: string;
}

const initialState: AnalysisState = {
  currentConfig: {
    travel_time: 15,
    travel_mode: TravelMode.WALK,
    geographic_level: GeographicLevel.BLOCK_GROUP,
    census_variables: ['B01003_001E'], // Total population
    include_isochrones: true,
    include_demographics: true,
  },
  validationErrors: {},
  activeJobs: [],
  recentAnalyses: [],
  currentStep: 0,
  isSubmitting: false,
};

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    // Configuration management
    updateConfiguration: (state, action: PayloadAction<Partial<AnalysisConfiguration>>) => {
      state.currentConfig = { ...state.currentConfig, ...action.payload };
      // Clear related validation errors
      Object.keys(action.payload).forEach(key => {
        delete state.validationErrors[key];
      });
    },

    resetConfiguration: (state) => {
      state.currentConfig = initialState.currentConfig;
      state.validationErrors = {};
      state.currentStep = 0;
    },

    // Validation
    setValidationError: (state, action: PayloadAction<{ field: string; message: string }>) => {
      state.validationErrors[action.payload.field] = action.payload.message;
    },

    clearValidationError: (state, action: PayloadAction<string>) => {
      delete state.validationErrors[action.payload];
    },

    clearAllValidationErrors: (state) => {
      state.validationErrors = {};
    },

    // Wizard navigation
    setCurrentStep: (state, action: PayloadAction<number>) => {
      state.currentStep = action.payload;
    },

    nextStep: (state) => {
      state.currentStep += 1;
    },

    previousStep: (state) => {
      if (state.currentStep > 0) {
        state.currentStep -= 1;
      }
    },

    // Job management
    addActiveJob: (state, action: PayloadAction<ActiveJob>) => {
      state.activeJobs = [action.payload, ...state.activeJobs];
    },

    updateJobStatus: (state, action: PayloadAction<{ id: string; status: JobStatusEnum; progress?: number; message?: string }>) => {
      const jobIndex = state.activeJobs.findIndex(job => job.id === action.payload.id);
      if (jobIndex !== -1) {
        state.activeJobs[jobIndex] = {
          ...state.activeJobs[jobIndex],
          ...action.payload,
          updated_at: new Date().toISOString(),
        };
      }
    },

    removeActiveJob: (state, action: PayloadAction<string>) => {
      state.activeJobs = state.activeJobs.filter(job => job.id !== action.payload);
    },

    completeJob: (state, action: PayloadAction<string>) => {
      const jobIndex = state.activeJobs.findIndex(job => job.id === action.payload);
      if (jobIndex !== -1) {
        // Move to recent analyses
        state.recentAnalyses = [action.payload, ...state.recentAnalyses.slice(0, 9)]; // Keep last 10
        state.activeJobs.splice(jobIndex, 1);
      }
    },

    // Submission state
    setSubmitting: (state, action: PayloadAction<boolean>) => {
      state.isSubmitting = action.payload;
    },

    // Demo scenarios
    selectDemoScenario: (state, action: PayloadAction<string>) => {
      state.selectedDemoScenario = action.payload;
    },

    // Quick configuration presets
    applyPreset: (state, action: PayloadAction<'quick_start' | 'detailed_analysis' | 'demographic_focus'>) => {
      const presets = {
        quick_start: {
          travel_time: 10,
          travel_mode: TravelMode.WALK,
          census_variables: ['B01003_001E'],
          include_isochrones: true,
          include_demographics: false,
        },
        detailed_analysis: {
          travel_time: 15,
          travel_mode: TravelMode.WALK,
          census_variables: ['B01003_001E', 'B19013_001E', 'B25003_001E'],
          include_isochrones: true,
          include_demographics: true,
        },
        demographic_focus: {
          travel_time: 20,
          travel_mode: TravelMode.WALK,
          census_variables: ['B01003_001E', 'B19013_001E', 'B08303_001E', 'B25003_001E'],
          include_isochrones: false,
          include_demographics: true,
        },
      };
      
      state.currentConfig = { ...state.currentConfig, ...presets[action.payload] };
    },
  },
});

export const {
  updateConfiguration,
  resetConfiguration,
  setValidationError,
  clearValidationError,
  clearAllValidationErrors,
  setCurrentStep,
  nextStep,
  previousStep,
  addActiveJob,
  updateJobStatus,
  removeActiveJob,
  completeJob,
  setSubmitting,
  selectDemoScenario,
  applyPreset,
} = analysisSlice.actions;

export default analysisSlice.reducer;