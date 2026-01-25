/**
 * Notification Settings Component
 * Manages email notification preferences
 * Requirements: 6.2.1, 6.2.2, 6.2.3, 6.2.4, 6.2.5
 */
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient } from '@/lib/api';

interface NotificationSettingsProps {
  onUpdate?: () => void;
  onChange?: () => void;
}

const NotificationSettings: React.FC<NotificationSettingsProps> = ({ onUpdate, onChange }) => {
  const [preferences, setPreferences] = useState({
    email: 'user@example.com',
    frequency: 'immediate',
    categories: {
      alerts: true,
      reports: true,
      policy_updates: true,
      claim_status: false,
    },
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      const response = await apiClient.get('/api/notifications/preferences');
      if (response.data) {
        setPreferences(response.data);
      }
    } catch (err) {
      console.error('Failed to load preferences:', err);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setSuccess(false);
    
    try {
      await apiClient.put('/api/notifications/preferences', preferences);
      setSuccess(true);
      onUpdate?.();
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || 'Failed to save preferences');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      {success && (
        <Alert>
          <AlertDescription>Preferences saved successfully!</AlertDescription>
        </Alert>
      )}
      
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email Address</Label>
          <Input
            id="email"
            type="email"
            value={preferences.email}
            onChange={(e) => {
              setPreferences({ ...preferences, email: e.target.value });
              onChange?.();
            }}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="frequency">Notification Frequency</Label>
          <Select
            value={preferences.frequency}
            onValueChange={(value) => {
              setPreferences({ ...preferences, frequency: value });
              onChange?.();
            }}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="immediate">Immediate</SelectItem>
              <SelectItem value="daily">Daily Digest</SelectItem>
              <SelectItem value="weekly">Weekly Summary</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          <Label>Notification Categories</Label>
          
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Alerts</p>
              <p className="text-sm text-muted-foreground">High-risk claims and system alerts</p>
            </div>
            <Switch
              checked={preferences.categories.alerts}
              onCheckedChange={(checked) => {
                setPreferences({
                  ...preferences,
                  categories: { ...preferences.categories, alerts: checked },
                });
                onChange?.();
              }}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Reports</p>
              <p className="text-sm text-muted-foreground">Daily and weekly reports</p>
            </div>
            <Switch
              checked={preferences.categories.reports}
              onCheckedChange={(checked) => {
                setPreferences({
                  ...preferences,
                  categories: { ...preferences.categories, reports: checked },
                });
                onChange?.();
              }}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Policy Updates</p>
              <p className="text-sm text-muted-foreground">Policy changes and expirations</p>
            </div>
            <Switch
              checked={preferences.categories.policy_updates}
              onCheckedChange={(checked) => {
                setPreferences({
                  ...preferences,
                  categories: { ...preferences.categories, policy_updates: checked },
                });
                onChange?.();
              }}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Claim Status</p>
              <p className="text-sm text-muted-foreground">Claim submissions and approvals</p>
            </div>
            <Switch
              checked={preferences.categories.claim_status}
              onCheckedChange={(checked) => {
                setPreferences({
                  ...preferences,
                  categories: { ...preferences.categories, claim_status: checked },
                });
                onChange?.();
              }}
            />
          </div>
        </div>
      </div>

      <Button onClick={handleSave} disabled={loading}>
        {loading ? 'Saving...' : 'Save Preferences'}
      </Button>
    </div>
  );
};

export default NotificationSettings;
