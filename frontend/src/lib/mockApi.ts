/**
 * Mock API Service for Local Development
 * Intercepts API calls and returns dummy data
 */

import {
  mockDashboardData,
  mockEligibilityData,
  mockBillAuditData,
  mockPoliciesData,
  mockPatientProfileData,
  mockReportsData,
  mockAuditLogsData,
  mockBatchData,
  mockWebhooksData,
  mockNotificationPreferences,
  mockUserProfile,
  mockVersionComparisonData,
  generateMockPatients,
  generateMockClaims,
} from './mockData';

// Enable/disable mock mode
export const MOCK_MODE = import.meta.env.VITE_MOCK_MODE === 'true' || !import.meta.env.VITE_API_URL;

// Simulate network delay
const delay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

// Mock API responses
export const mockApi = {
  // Authentication
  async login(email: string, password: string) {
    await delay();
    if (email && password) {
      return {
        success: true,
        token: 'mock-jwt-token-' + Date.now(),
        user: mockUserProfile,
        mfa_required: false,
      };
    }
    throw new Error('Invalid credentials');
  },

  async logout() {
    await delay(200);
    return { success: true };
  },

  // Dashboard
  async getDashboard() {
    await delay();
    return mockDashboardData;
  },

  // Eligibility Check
  async checkEligibility(patientId: string, policyNumber: string) {
    await delay();
    return {
      ...mockEligibilityData,
      patient_id: patientId,
      policy_number: policyNumber,
    };
  },

  async batchEligibilityCheck(file: File) {
    await delay(1000);
    return mockBatchData;
  },

  async getBatchStatus(batchId: string) {
    await delay();
    return {
      ...mockBatchData,
      batch_id: batchId,
      processed: Math.min(mockBatchData.processed + 10, mockBatchData.total_records),
    };
  },

  // Bill Audit
  async auditBill(claimId: string) {
    await delay(800);
    return {
      ...mockBillAuditData,
      claim_id: claimId,
    };
  },

  // Policy Management
  async getPolicies(filters?: any) {
    await delay();
    return {
      policies: mockPoliciesData,
      total: mockPoliciesData.length,
    };
  },

  async getPolicy(policyId: string) {
    await delay();
    return mockPoliciesData.find(p => p.policy_id === policyId) || mockPoliciesData[0];
  },

  async createPolicy(policyData: any) {
    await delay();
    return {
      success: true,
      policy_id: 'POL-' + Date.now(),
      ...policyData,
    };
  },

  async updatePolicy(policyId: string, policyData: any) {
    await delay();
    return {
      success: true,
      policy_id: policyId,
      ...policyData,
    };
  },

  async deletePolicy(policyId: string) {
    await delay();
    return { success: true };
  },

  async getPolicyVersions(policyId: string) {
    await delay();
    return mockVersionComparisonData;
  },

  async compareVersions(policyId: string, v1: number, v2: number) {
    await delay();
    return mockVersionComparisonData.comparison;
  },

  async rollbackPolicy(policyId: string, version: number) {
    await delay();
    return { success: true, version };
  },

  // Patient Profile
  async getPatientProfile(patientId: string) {
    await delay();
    return {
      ...mockPatientProfileData,
      patient_id: patientId,
    };
  },

  async getPatientClaims(patientId: string) {
    await delay();
    return mockPatientProfileData.claims;
  },

  async getPatientRiskAnalytics(patientId: string) {
    await delay();
    return mockPatientProfileData.risk_analytics;
  },

  // Reports
  async getReports(params?: any) {
    await delay();
    return mockReportsData;
  },

  async generateReport(reportType: string, params: any) {
    await delay(1500);
    return {
      success: true,
      report_id: 'RPT-' + Date.now(),
      download_url: '/mock-report.pdf',
    };
  },

  // Audit Logs
  async getAuditLogs(filters?: any) {
    await delay();
    return {
      logs: mockAuditLogsData,
      total: mockAuditLogsData.length,
    };
  },

  // Webhooks
  async getWebhooks() {
    await delay();
    return {
      webhooks: mockWebhooksData,
    };
  },

  async createWebhook(webhookData: any) {
    await delay();
    return {
      success: true,
      webhook_id: 'WH-' + Date.now(),
      ...webhookData,
    };
  },

  async updateWebhook(webhookId: string, webhookData: any) {
    await delay();
    return {
      success: true,
      webhook_id: webhookId,
      ...webhookData,
    };
  },

  async deleteWebhook(webhookId: string) {
    await delay();
    return { success: true };
  },

  async testWebhook(webhookData: any) {
    await delay(1000);
    return {
      success: true,
      status_code: 200,
      response_time_ms: 245,
      response_body: '{"status":"ok"}',
    };
  },

  async getWebhookActivity(webhookId: string) {
    await delay();
    return {
      deliveries: [
        {
          delivery_id: 'DEL-001',
          event_type: 'claim_submitted',
          status: 'success',
          status_code: 200,
          response_time_ms: 234,
          timestamp: new Date().toISOString(),
        },
        {
          delivery_id: 'DEL-002',
          event_type: 'high_risk_detected',
          status: 'failed',
          status_code: 500,
          response_time_ms: 1234,
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          error: 'Internal server error',
        },
      ],
    };
  },

  // Notifications
  async getNotificationPreferences() {
    await delay();
    return mockNotificationPreferences;
  },

  async updateNotificationPreferences(preferences: any) {
    await delay();
    return {
      success: true,
      ...preferences,
    };
  },

  // User Profile
  async getUserProfile() {
    await delay();
    return mockUserProfile;
  },

  async updateUserProfile(profileData: any) {
    await delay();
    return {
      success: true,
      ...mockUserProfile,
      ...profileData,
    };
  },

  async changePassword(currentPassword: string, newPassword: string) {
    await delay();
    if (currentPassword && newPassword) {
      return { success: true };
    }
    throw new Error('Invalid password');
  },

  // Search
  async searchPatients(query: string) {
    await delay();
    const patients = generateMockPatients(50);
    return patients.filter(p => 
      p.name.toLowerCase().includes(query.toLowerCase()) ||
      p.patient_id.includes(query) ||
      p.policy_number.includes(query)
    ).slice(0, 10);
  },

  async searchPolicies(query: string) {
    await delay();
    return mockPoliciesData.filter(p =>
      p.policy_number.includes(query) ||
      p.policy_holder.toLowerCase().includes(query.toLowerCase())
    );
  },

  async searchClaims(query: string) {
    await delay();
    const claims = generateMockClaims(100);
    return claims.filter(c =>
      c.claim_id.includes(query) ||
      c.patient_name.toLowerCase().includes(query.toLowerCase()) ||
      c.policy_number.includes(query)
    ).slice(0, 10);
  },
};

// API interceptor
export const createMockApiClient = () => {
  return {
    get: async (url: string, config?: any) => {
      console.log('[MOCK API] GET', url);
      
      // Dashboard
      if (url.includes('/dashboard')) {
        return { data: await mockApi.getDashboard() };
      }
      
      // Eligibility
      if (url.includes('/eligibility/check')) {
        return { data: await mockApi.checkEligibility('PAT-12345', 'POL-12345') };
      }
      
      // Policies
      if (url.includes('/policies') && !url.includes('/versions')) {
        const policyId = url.split('/').pop();
        if (policyId && policyId !== 'policies') {
          return { data: await mockApi.getPolicy(policyId) };
        }
        return { data: await mockApi.getPolicies() };
      }
      
      // Policy Versions
      if (url.includes('/versions')) {
        const policyId = url.split('/')[2];
        return { data: await mockApi.getPolicyVersions(policyId) };
      }
      
      // Patient Profile
      if (url.includes('/patients/')) {
        const patientId = url.split('/')[2];
        if (url.includes('/claims')) {
          return { data: await mockApi.getPatientClaims(patientId) };
        }
        if (url.includes('/risk')) {
          return { data: await mockApi.getPatientRiskAnalytics(patientId) };
        }
        return { data: await mockApi.getPatientProfile(patientId) };
      }
      
      // Reports
      if (url.includes('/reports')) {
        return { data: await mockApi.getReports() };
      }
      
      // Audit Logs
      if (url.includes('/audit-logs')) {
        return { data: await mockApi.getAuditLogs() };
      }
      
      // Webhooks
      if (url.includes('/webhooks')) {
        if (url.includes('/activity')) {
          const webhookId = url.split('/')[2];
          return { data: await mockApi.getWebhookActivity(webhookId) };
        }
        return { data: await mockApi.getWebhooks() };
      }
      
      // Notifications
      if (url.includes('/notifications/preferences')) {
        return { data: await mockApi.getNotificationPreferences() };
      }
      
      // User Profile
      if (url.includes('/user/profile')) {
        return { data: await mockApi.getUserProfile() };
      }
      
      return { data: {} };
    },
    
    post: async (url: string, data?: any, config?: any) => {
      console.log('[MOCK API] POST', url, data);
      
      // Login
      if (url.includes('/auth/login')) {
        return { data: await mockApi.login(data.email, data.password) };
      }
      
      // Logout
      if (url.includes('/auth/logout')) {
        return { data: await mockApi.logout() };
      }
      
      // Eligibility Check
      if (url.includes('/eligibility/check')) {
        return { data: await mockApi.checkEligibility(data.patient_id, data.policy_number) };
      }
      
      // Batch Eligibility
      if (url.includes('/eligibility/batch')) {
        return { data: await mockApi.batchEligibilityCheck(data) };
      }
      
      // Bill Audit
      if (url.includes('/audit/bill')) {
        return { data: await mockApi.auditBill(data.claim_id) };
      }
      
      // Create Policy
      if (url.includes('/policies') && !url.includes('/')) {
        return { data: await mockApi.createPolicy(data) };
      }
      
      // Webhook Test
      if (url.includes('/webhooks/test')) {
        return { data: await mockApi.testWebhook(data) };
      }
      
      // Generate Report
      if (url.includes('/reports/generate')) {
        return { data: await mockApi.generateReport(data.type, data.params) };
      }
      
      return { data: { success: true } };
    },
    
    put: async (url: string, data?: any, config?: any) => {
      console.log('[MOCK API] PUT', url, data);
      
      // Update Policy
      if (url.includes('/policies/')) {
        const policyId = url.split('/')[2];
        return { data: await mockApi.updatePolicy(policyId, data) };
      }
      
      // Update Webhook
      if (url.includes('/webhooks/')) {
        const webhookId = url.split('/')[2];
        return { data: await mockApi.updateWebhook(webhookId, data) };
      }
      
      // Update Notification Preferences
      if (url.includes('/notifications/preferences')) {
        return { data: await mockApi.updateNotificationPreferences(data) };
      }
      
      // Update User Profile
      if (url.includes('/user/profile')) {
        return { data: await mockApi.updateUserProfile(data) };
      }
      
      return { data: { success: true } };
    },
    
    delete: async (url: string, config?: any) => {
      console.log('[MOCK API] DELETE', url);
      
      // Delete Policy
      if (url.includes('/policies/')) {
        const policyId = url.split('/')[2];
        return { data: await mockApi.deletePolicy(policyId) };
      }
      
      // Delete Webhook
      if (url.includes('/webhooks/')) {
        const webhookId = url.split('/')[2];
        return { data: await mockApi.deleteWebhook(webhookId) };
      }
      
      return { data: { success: true } };
    },
  };
};
