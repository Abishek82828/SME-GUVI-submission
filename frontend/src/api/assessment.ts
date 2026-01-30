import { request } from './client';
import { AssessmentResponse } from '../types';

export const healthCheck = async (): Promise<any> => {
  // Fixed: Endpoint is /api/health per backend contract
  return request('/api/health');
};

export const createAssessment = async (formData: FormData): Promise<AssessmentResponse> => {
  // Do not set Content-Type header manually for FormData; fetch handles it including boundary
  return request<AssessmentResponse>('/api/assessments', {
    method: 'POST',
    body: formData,
  });
};

export const getAssessment = async (id: string): Promise<AssessmentResponse> => {
  return request<AssessmentResponse>(`/api/assessments/${id}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });
};

export const getAssessmentReport = async (id: string): Promise<string> => {
  // Fixed: Backend returns JSON { id, report_md }, we must extract report_md
  const response = await request<{ report_md: string }>(`/api/assessments/${id}/report`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });
  return response.report_md || '';
};

export const getAssessmentAI = async (id: string): Promise<string> => {
  // Added: Backend returns JSON { id, ai_md }, we must extract ai_md
  const response = await request<{ ai_md: string }>(`/api/assessments/${id}/ai`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });
  return response.ai_md || '';
};