import { configureStore } from '@reduxjs/toolkit';
import evaluationReducer from './evaluationSlice';

export const store = configureStore({
  reducer: {
    evaluation: evaluationReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
}); 