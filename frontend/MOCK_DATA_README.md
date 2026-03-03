# Mock Data Setup for Local Development

This project includes a comprehensive mock data system that allows you to run and test the frontend without deploying the AWS backend.

## Quick Start

The mock mode is **enabled by default** for local development. Just run:

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 and you'll see the application with dummy data.

## Mock Mode Configuration

Mock mode is controlled by the `.env` file:

```env
# Enable mock mode (default: true)
VITE_MOCK_MODE=true
```

When `VITE_MOCK_MODE=true` or `VITE_API_URL` is not set, the application automatically uses mock data.

## Available Mock Data

### 1. Dashboard
- Total claims: 1,247
- Pending reviews: 89
- High-risk claims: 23
- Recent claims list
- System alerts

### 2. Eligibility Check
- Patient information
- Policy status and coverage details
- Coverage limits and usage
- Deductible information

### 3. Bill Audit
- Audit results with discrepancies
- Approved vs billed amounts
- Recommendations
- Audit history

### 4. Policy Management
- 3 sample policies (Individual, Family, Senior Citizen)
- Policy versions and history
- Version comparison
- Rollback functionality

### 5. Patient Profile
- Patient demographics
- Claim history (12 claims)
- Risk analytics and trends
- Multi-claim analysis
- Recommendations

### 6. Reports
- Claims summary (last 30 days)
- Claims by status and type
- Top procedures
- Risk distribution

### 7. Audit Logs
- User actions log
- Login attempts
- Policy updates
- Claim submissions

### 8. Batch Processing
- CSV upload simulation
- Processing progress
- Success/failure results
- 150 sample records

### 9. Webhooks
- 2 configured webhooks
- Delivery logs
- Test functionality
- Activity tracking

### 10. Settings
- Notification preferences
- User profile
- Webhook configuration

## Login Credentials

In mock mode, you can login with **any email and password**. For example:

- Email: `admin@hospital.com`
- Password: `any password`

The mock system will return a successful login with admin user profile.

## Mock API Features

### Realistic Delays
All mock API calls include realistic network delays (200-1500ms) to simulate real API behavior.

### Console Logging
All mock API calls are logged to the browser console with `[MOCK API]` prefix for debugging.

### Data Generation
The mock system can generate additional data on demand:
- `generateMockPatients(count)` - Generate N patients
- `generateMockClaims(count)` - Generate N claims

## Switching to Real Backend

When you're ready to connect to the real AWS backend:

1. Deploy your backend to AWS:
   ```bash
   cd hospital-claim-optimizer
   ./deploy.sh
   ```

2. Update `.env` file:
   ```env
   VITE_MOCK_MODE=false
   VITE_API_URL=https://your-api-gateway-url.amazonaws.com/prod
   VITE_COGNITO_USER_POOL_ID=your-user-pool-id
   VITE_COGNITO_CLIENT_ID=your-client-id
   ```

3. Restart the development server:
   ```bash
   npm run dev
   ```

## Mock Data Files

- `src/lib/mockData.ts` - All dummy data definitions
- `src/lib/mockApi.ts` - Mock API implementation
- `src/lib/api.ts` - API client with mock mode support

## Customizing Mock Data

To add or modify mock data:

1. Edit `src/lib/mockData.ts` to add new data
2. Update `src/lib/mockApi.ts` to add new API endpoints
3. The changes will be hot-reloaded automatically

Example:
```typescript
// In mockData.ts
export const mockNewFeatureData = {
  feature_id: 'FEAT-001',
  name: 'New Feature',
  // ... more data
};

// In mockApi.ts
export const mockApi = {
  // ... existing methods
  async getNewFeature() {
    await delay();
    return mockNewFeatureData;
  },
};
```

## Testing Different Scenarios

You can modify mock data to test different scenarios:

### High-Risk Claims
Edit `mockDashboardData.recentClaims` to add more high-risk claims with `risk_score > 0.7`.

### Policy Expiration
Edit `mockPoliciesData` to set `end_date` to near-future dates.

### Failed Webhooks
Edit `mockWebhookActivity` to add more failed deliveries.

### Batch Processing Errors
Edit `mockBatchData.results` to add more error cases.

## Benefits of Mock Mode

1. **No AWS Setup Required** - Start developing immediately
2. **Fast Iteration** - No network latency
3. **Offline Development** - Work without internet
4. **Predictable Data** - Same data every time
5. **Easy Testing** - Test edge cases easily
6. **Cost Savings** - No AWS charges during development

## Troubleshooting

### Mock mode not working?
Check the browser console for `[API Client] Mock mode: ENABLED` message.

### Data not showing?
Open browser DevTools and check for `[MOCK API]` logs to see which endpoints are being called.

### Want to add more data?
Edit `mockData.ts` and add your data. The mock API will automatically use it.

## Demo Mode

For hackathon demos or presentations, mock mode is perfect because:
- Data is consistent and predictable
- No dependency on AWS services
- Fast response times
- No risk of API failures
- Can demo offline

---

**Happy Coding!** 🚀
