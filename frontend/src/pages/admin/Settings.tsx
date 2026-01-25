/**
 * Settings Page
 * Provides configuration interface for system settings
 * Requirements: 3.1.1, 3.1.2, 3.1.3, 3.1.4, 3.1.5
 */
import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Settings as SettingsIcon, Webhook, Bell, User, Clock } from 'lucide-react';
import WebhookSettings from '@/components/settings/WebhookSettings';
import NotificationSettings from '@/components/settings/NotificationSettings';
import ProfileSettings from '@/components/settings/ProfileSettings';

interface SettingsPageProps {
  userRole?: string;
}

const SettingsPage: React.FC<SettingsPageProps> = ({ userRole = 'admin' }) => {
  const [activeTab, setActiveTab] = useState('integrations');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Check if user has admin access
  const isAdmin = userRole === 'admin' || userRole === 'tpa_admin' || userRole === 'hospital_admin';

  if (!isAdmin) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>
            You do not have permission to access settings. Only administrators can configure system settings.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const handleSettingsUpdate = () => {
    setLastUpdated(new Date());
    setHasUnsavedChanges(false);
  };

  const handleChange = () => {
    setHasUnsavedChanges(true);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <SettingsIcon className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-3xl font-bold">Settings</h1>
            <p className="text-muted-foreground">
              Configure system integrations, notifications, and preferences
            </p>
          </div>
        </div>
        
        {lastUpdated && (
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>
              Last updated: {lastUpdated.toLocaleString()}
            </span>
          </div>
        )}
      </div>

      {/* Unsaved Changes Warning */}
      {hasUnsavedChanges && (
        <Alert>
          <AlertDescription>
            You have unsaved changes. Make sure to save your changes before leaving this page.
          </AlertDescription>
        </Alert>
      )}

      {/* Settings Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 lg:w-[600px]">
          <TabsTrigger value="integrations" className="flex items-center space-x-2">
            <Webhook className="h-4 w-4" />
            <span>Integrations</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center space-x-2">
            <Bell className="h-4 w-4" />
            <span>Notifications</span>
          </TabsTrigger>
          <TabsTrigger value="profile" className="flex items-center space-x-2">
            <User className="h-4 w-4" />
            <span>Profile</span>
          </TabsTrigger>
        </TabsList>

        {/* Integrations Tab */}
        <TabsContent value="integrations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Webhook Integrations</CardTitle>
              <CardDescription>
                Configure webhooks to send real-time notifications to external systems
              </CardDescription>
            </CardHeader>
            <CardContent>
              <WebhookSettings 
                onUpdate={handleSettingsUpdate}
                onChange={handleChange}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Email Notifications</CardTitle>
              <CardDescription>
                Manage your email notification preferences and delivery settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <NotificationSettings 
                onUpdate={handleSettingsUpdate}
                onChange={handleChange}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Profile Settings</CardTitle>
              <CardDescription>
                Manage your account settings, password, and security preferences
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ProfileSettings 
                onUpdate={handleSettingsUpdate}
                onChange={handleChange}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SettingsPage;
