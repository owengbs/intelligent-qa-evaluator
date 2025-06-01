import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { evaluationService } from '../services/evaluationService';

// 异步thunk：提交评估请求
export const submitEvaluation = createAsyncThunk(
  'evaluation/submit',
  async (evaluationData, { rejectWithValue }) => {
    try {
      console.log('Redux: 开始提交评估请求', evaluationData);
      const result = await evaluationService.evaluate(evaluationData);
      console.log('Redux: 评估请求成功', result);
      return result;
    } catch (error) {
      console.error('Redux: 评估请求失败', error);
      return rejectWithValue(error.message);
    }
  }
);

const evaluationSlice = createSlice({
  name: 'evaluation',
  initialState: {
    isLoading: false,
    result: null,
    error: null,
    history: [], // 评估历史记录
  },
  reducers: {
    clearResult: (state) => {
      state.result = null;
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    },
    clearHistory: (state) => {
      state.history = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitEvaluation.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(submitEvaluation.fulfilled, (state, action) => {
        state.isLoading = false;
        state.result = action.payload;
        // 添加到历史记录
        state.history.unshift({
          ...action.payload,
          id: Date.now(),
        });
        // 保持最多10条历史记录
        if (state.history.length > 10) {
          state.history = state.history.slice(0, 10);
        }
      })
      .addCase(submitEvaluation.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });
  },
});

export const { clearResult, clearError, clearHistory } = evaluationSlice.actions;
export default evaluationSlice.reducer; 