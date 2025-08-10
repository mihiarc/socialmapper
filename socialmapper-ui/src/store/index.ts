/**
 * Redux store configuration with RTK Query for SocialMapper
 * Provides centralized state management and API caching
 */
import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';

import { analysisApi } from './api/analysisApi';
import { metadataApi } from './api/metadataApi';
import analysisSlice from './slices/analysisSlice';
import uiSlice from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    // RTK Query APIs
    [analysisApi.reducerPath]: analysisApi.reducer,
    [metadataApi.reducerPath]: metadataApi.reducer,
    
    // Feature slices
    analysis: analysisSlice,
    ui: uiSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types for non-serializable values
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    })
      .concat(analysisApi.middleware)
      .concat(metadataApi.middleware),
  
  devTools: process.env.NODE_ENV !== 'production',
});

// Enable listener behavior for the store
setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;