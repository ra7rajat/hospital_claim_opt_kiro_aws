# Hospital Insurance Claim Settlement Optimizer - Frontend

This is the frontend application for the Hospital Insurance Claim Settlement Optimizer, built with React, TypeScript, Vite, and Tailwind CSS.

## Tech Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **TanStack Query (React Query)** - Server state management
- **Lucide React** - Icon library

## Project Structure

```
src/
├── components/       # Reusable UI components
│   └── Layout.tsx   # Main layout with navigation
├── pages/           # Page components
│   ├── admin/       # Admin role pages
│   │   ├── Dashboard.tsx
│   │   ├── PolicyManagement.tsx
│   │   └── Reports.tsx
│   ├── doctor/      # Doctor role pages
│   │   └── EligibilityCheck.tsx
│   ├── billing/     # Billing specialist pages
│   │   └── BillAudit.tsx
│   └── Login.tsx    # Login page
├── lib/             # Utility libraries
│   ├── api.ts       # API client
│   ├── queryClient.ts # React Query configuration
│   └── utils.ts     # Utility functions
├── types/           # TypeScript type definitions
│   └── auth.ts      # Authentication types
├── router.tsx       # Route configuration
├── App.tsx          # Root component
└── main.tsx         # Application entry point
```

## User Roles and Routes

The application supports multiple user roles with dedicated interfaces:

- **Admin/TPA Manager**: `/admin/*`
  - Dashboard: `/admin/dashboard`
  - Policy Management: `/admin/policies`
  - Reports & Analytics: `/admin/reports`

- **Doctor**: `/doctor/*`
  - Eligibility Check: `/doctor/eligibility`

- **Billing Specialist**: `/billing/*`
  - Bill Audit: `/billing/audit`

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Environment Variables

Create a `.env` file in the frontend directory:

```
VITE_API_BASE_URL=http://localhost:3000/api
```

See `.env.example` for reference.

## Features Implemented

- ✅ React + TypeScript + Vite setup
- ✅ Tailwind CSS configuration
- ✅ React Query for server state management
- ✅ API client with authentication support
- ✅ Layout component with navigation
- ✅ Page structure for all user roles
- ✅ TypeScript types for authentication

## Next Steps

The following features will be implemented in subsequent tasks:

- Policy upload and management interface
- Real-time eligibility checking for doctors
- Bill audit interface with AI-powered analysis
- TPA Command Center dashboard with analytics
- Reporting and visualization components
- Authentication and authorization flows
