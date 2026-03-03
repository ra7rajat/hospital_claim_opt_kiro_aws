# Running the Hospital Claim Optimizer Project

**Author:** Rajat Dixit  
**Repository:** https://github.com/ra7rajat/hospital_claim_opt_kiro_aws  
**Last Updated:** January 25, 2026

## 🚀 Quick Start (Mock Mode - No AWS Required)

The easiest way to run the project is using **Mock Mode** with dummy data:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies (if not already done)
npm install

# 3. Start the development server
npm run dev
```

**That's it!** Open http://localhost:5173 in your browser.

### Login Credentials (Mock Mode)
- **Email:** Any email (e.g., `admin@hospital.com`)
- **Password:** Any password

The mock system will automatically log you in with an admin profile.

## 📊 What You'll See

With mock mode enabled, you'll have access to:

### Dashboard
- 1,247 total claims
- 89 pending reviews
- 23 high-risk claims
- Real-time alerts
- Claims trends and analytics

### Eligibility Check
- Check patient eligibility
- View coverage details
- See deductible information
- Batch processing (CSV upload)

### Bill Audit
- Audit claim bills
- View discrepancies
- Get recommendations
- See audit history

### Policy Management
- 3 sample policies
- Version control
- Policy comparison
- Rollback functionality

### Patient Profile
- Patient demographics
- 12 sample claims
- Risk analytics
- Multi-claim analysis
- Recommendations

### Reports
- Claims summary
- Status distribution
- Top procedures
- Risk analysis

### Admin Features
- Audit logs
- Webhook configuration
- Notification settings
- User profile management

## 🎯 Mock Mode Features

### Realistic Behavior
- Network delays (200-1500ms)
- Loading states
- Error handling
- Success/failure scenarios

### Console Logging
All API calls are logged with `[MOCK API]` prefix for debugging.

### Predictable Data
Same data every time - perfect for:
- Development
- Testing
- Demos
- Presentations
- Hackathons

## 🔧 Project Architecture

### Frontend (Currently Running)
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **UI:** Custom components + Tailwind CSS
- **Port:** http://localhost:5173

### Backend (Serverless - AWS)
- **Compute:** AWS Lambda (Python)
- **API:** API Gateway
- **Database:** DynamoDB
- **Cache:** ElastiCache
- **Auth:** Cognito
- **Storage:** S3

## 📁 Project Structure

```
hospital_claim_opt_kiro_aws/
├── frontend/                    # React frontend (RUNNING)
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── pages/              # Page components
│   │   ├── lib/
│   │   │   ├── mockData.ts    # Dummy data
│   │   │   ├── mockApi.ts     # Mock API
│   │   │   └── api.ts         # API client
│   │   └── ...
│   ├── .env                    # VITE_MOCK_MODE=true
│   └── package.json
│
├── hospital-claim-optimizer/   # AWS backend
│   ├── lambda-functions/       # Lambda handlers
│   ├── lambda-layers/          # Shared code
│   ├── lib/                    # CDK stack
│   └── deploy.sh              # Deployment script
│
└── e2e/                        # End-to-end tests
```

## 🎮 Using the Application

### 1. Dashboard
Navigate to the dashboard to see:
- System metrics
- Recent claims
- Alerts
- Quick actions

### 2. Check Eligibility
Go to **Eligibility Check** page:
- Enter patient ID and policy number
- Click "Check Eligibility"
- View coverage details

### 3. Audit Bills
Go to **Bill Audit** page:
- Enter claim ID
- Click "Audit Bill"
- Review discrepancies and recommendations

### 4. Manage Policies
Go to **Policy Management** page:
- View all policies
- Search and filter
- Create/edit/delete policies
- Compare versions

### 5. View Patient Profile
Go to **Patient Profile** page:
- Enter patient ID
- View claim history
- See risk analytics
- Review recommendations

### 6. Generate Reports
Go to **Reports** page:
- Select report type
- Choose date range
- Generate and download

### 7. Admin Settings
Go to **Settings** page:
- Configure notifications
- Manage webhooks
- Update profile

## 🔄 Switching to Real AWS Backend

When ready to use the real backend:

### Step 1: Deploy to AWS
```bash
cd hospital-claim-optimizer
./deploy.sh
```

This will:
- Build CDK stack
- Deploy Lambda functions
- Configure API Gateway
- Set up DynamoDB
- Configure Cognito
- Deploy CloudFront

### Step 2: Update Environment
Edit `frontend/.env`:
```env
VITE_MOCK_MODE=false
VITE_API_URL=https://your-api-gateway-url.amazonaws.com/prod
VITE_COGNITO_USER_POOL_ID=your-user-pool-id
VITE_COGNITO_CLIENT_ID=your-client-id
```

### Step 3: Restart Frontend
```bash
cd frontend
npm run dev
```

## 🧪 Testing

### Frontend Linting
```bash
cd frontend
npm run lint
```

### Backend Tests
```bash
cd hospital-claim-optimizer
pytest tests/
```

### End-to-End Tests
```bash
cd e2e
npx playwright test
```

## 📝 Development Tips

### Hot Reload
The frontend has hot module replacement (HMR). Changes to code will automatically reload.

### Mock Data Customization
Edit `frontend/src/lib/mockData.ts` to modify dummy data.

### Adding New Mock Endpoints
Edit `frontend/src/lib/mockApi.ts` to add new API endpoints.

### Debugging
- Open browser DevTools (F12)
- Check Console for `[MOCK API]` logs
- Check Network tab (will be empty in mock mode)

## 🎯 For Hackathon/Demo

Mock mode is perfect for hackathons because:

1. **No Setup Time** - Start immediately
2. **No AWS Costs** - Free to run
3. **Offline Demo** - Works without internet
4. **Predictable** - Same data every time
5. **Fast** - No network latency
6. **Reliable** - No API failures

## 📚 Documentation

- **README.md** - Project overview
- **MOCK_DATA_README.md** - Mock data details
- **PROJECT_STATUS.md** - Current status
- **TECHNICAL_DOCUMENTATION.md** - Technical details
- **USER_GUIDE.md** - User documentation
- **DEPLOYMENT_GUIDE.md** - AWS deployment

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9

# Or use a different port
npm run dev -- --port 3000
```

### Mock Mode Not Working
Check browser console for:
```
[API Client] Mock mode: ENABLED
```

If you see `DISABLED`, check your `.env` file.

### No Data Showing
1. Open browser DevTools
2. Check Console for errors
3. Look for `[MOCK API]` logs
4. Verify mock mode is enabled

### Dependencies Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 🎉 Success Indicators

You'll know everything is working when you see:

1. ✅ Frontend server running at http://localhost:5173
2. ✅ Login page loads
3. ✅ Can login with any credentials
4. ✅ Dashboard shows metrics and claims
5. ✅ All pages are accessible
6. ✅ Console shows `[MOCK API]` logs

## 📞 Support

For issues:
1. Check browser console for errors
2. Review documentation files
3. Check GitHub issues
4. Review code comments

## 🚀 Next Steps

1. **Explore the UI** - Click around and test features
2. **Customize Mock Data** - Edit mockData.ts
3. **Add Features** - Build new components
4. **Deploy to AWS** - When ready for production
5. **Share with Team** - Push to GitHub

---

**Status:** ✅ RUNNING  
**Mode:** Mock (Dummy Data)  
**URL:** http://localhost:5173  
**Ready for:** Development, Testing, Demo, Hackathon

**Happy Coding!** 🎊
