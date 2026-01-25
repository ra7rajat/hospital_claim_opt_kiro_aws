import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks for better caching
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'query-vendor': ['@tanstack/react-query'],
          'chart-vendor': ['recharts'],
          // Feature-based chunks for code splitting
          'admin-pages': [
            './src/pages/admin/Dashboard.tsx',
            './src/pages/admin/PolicyManagement.tsx',
            './src/pages/admin/Reports.tsx',
            './src/pages/admin/AuditLogs.tsx',
            './src/pages/admin/Settings.tsx',
          ],
          'doctor-pages': [
            './src/pages/doctor/EligibilityCheck.tsx',
          ],
          'billing-pages': [
            './src/pages/billing/BillAudit.tsx',
            './src/pages/billing/PatientProfile.tsx',
          ],
        },
      },
    },
    // Optimize chunk size
    chunkSizeWarningLimit: 1000,
    // Enable minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.log in production
      },
    },
  },
  // Enable compression
  server: {
    compress: true,
  },
})
