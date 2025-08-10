/**
 * Feedback API slice for RTK Query
 * Handles feedback submission, analytics tracking, and feature requests
 */
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type {
  FeedbackRequest,
  FeedbackResponse,
  FeedbackSummary,
  UserAnalyticsEvent,
  FeatureRequest,
  FeatureVoteRequest,
  FeatureVote,
  InterviewRequest,
  InterviewSession,
  AnalyticsSummary,
  FeedbackInsights,
  BaseResponse,
} from "@/types/api";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

export const feedbackApi = createApi({
  reducerPath: 'feedbackApi',
  baseQuery: fetchBaseQuery({
    baseUrl: `${API_BASE_URL}/`,
    prepareHeaders: (headers) => {
      // Add any authentication headers if needed
      const token = localStorage.getItem('auth_token');
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Feedback', 'Analytics', 'FeatureRequest', 'Interview'],
  
  endpoints: (builder) => ({
    // Feedback endpoints
    submitFeedback: builder.mutation<FeedbackResponse, FeedbackRequest>({
      query: (feedback) => ({
        url: 'feedback',
        method: 'POST',
        body: feedback,
      }),
      invalidatesTags: ['Feedback'],
    }),

    getFeedbackSummary: builder.query<
      FeedbackSummary,
      { days?: number; touchpoint?: string }
    >({
      query: ({ days = 30, touchpoint } = {}) => ({
        url: 'feedback/summary',
        params: { days, ...(touchpoint && { touchpoint }) },
      }),
      providesTags: ['Feedback'],
    }),

    // Analytics endpoints
    trackAnalyticsEvent: builder.mutation<
      { status: string; message: string },
      UserAnalyticsEvent
    >({
      query: (event) => ({
        url: 'analytics/events',
        method: 'POST',
        body: event,
      }),
      invalidatesTags: ['Analytics'],
    }),

    getAnalyticsSummary: builder.query<
      AnalyticsSummary,
      { days?: number }
    >({
      query: ({ days = 30 } = {}) => ({
        url: 'analytics/summary',
        params: { days },
      }),
      providesTags: ['Analytics'],
    }),

    // Feature request endpoints
    createFeatureRequest: builder.mutation<
      FeatureRequest,
      Omit<FeatureRequest, 'id' | 'votes' | 'status' | 'created_at' | 'updated_at' | 'success' | 'timestamp'>
    >({
      query: (feature) => ({
        url: 'features',
        method: 'POST',
        body: feature,
      }),
      invalidatesTags: ['FeatureRequest'],
    }),

    listFeatureRequests: builder.query<
      FeatureRequest[],
      {
        limit?: number;
        offset?: number;
        category?: string;
        status?: string;
      }
    >({
      query: ({ limit = 50, offset = 0, category, status } = {}) => ({
        url: 'features',
        params: {
          limit,
          offset,
          ...(category && { category }),
          ...(status && { status }),
        },
      }),
      providesTags: ['FeatureRequest'],
    }),

    voteOnFeature: builder.mutation<FeatureVote, FeatureVoteRequest>({
      query: (vote) => ({
        url: 'features/vote',
        method: 'POST',
        body: vote,
      }),
      invalidatesTags: ['FeatureRequest'],
    }),

    // Interview endpoints
    requestInterview: builder.mutation<InterviewSession, InterviewRequest>({
      query: (interview) => ({
        url: 'interviews',
        method: 'POST',
        body: interview,
      }),
      invalidatesTags: ['Interview'],
    }),

    listInterviews: builder.query<
      InterviewSession[],
      {
        limit?: number;
        status?: string;
        interview_type?: string;
      }
    >({
      query: ({ limit = 50, status, interview_type } = {}) => ({
        url: 'interviews',
        params: {
          limit,
          ...(status && { status }),
          ...(interview_type && { interview_type }),
        },
      }),
      providesTags: ['Interview'],
    }),

    // Insights endpoints
    getFeedbackInsights: builder.query<
      FeedbackInsights,
      { days?: number }
    >({
      query: ({ days = 30 } = {}) => ({
        url: 'insights',
        params: { days },
      }),
      providesTags: ['Feedback', 'Analytics'],
    }),
  }),
});

export const {
  useSubmitFeedbackMutation,
  useGetFeedbackSummaryQuery,
  useTrackAnalyticsEventMutation,
  useGetAnalyticsSummaryQuery,
  useCreateFeatureRequestMutation,
  useListFeatureRequestsQuery,
  useVoteOnFeatureMutation,
  useRequestInterviewMutation,
  useListInterviewsQuery,
  useGetFeedbackInsightsQuery,
} = feedbackApi;