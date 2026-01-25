/**
 * Profile Settings Component
 * Manages user profile and security settings
 */
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';

interface ProfileSettingsProps {
  onUpdate?: () => void;
  onChange?: () => void;
}

const ProfileSettings: React.FC<ProfileSettingsProps> = ({ onUpdate, onChange }) => {
  const [profile, setProfile] = useState({
    name: 'John Doe',
    email: 'john.doe@example.com',
    role: 'Admin',
  });

  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const handleSaveProfile = () => {
    // TODO: Implement save logic
    onUpdate?.();
  };

  const handleChangePassword = () => {
    // TODO: Implement password change logic
    onUpdate?.();
  };

  return (
    <div className="space-y-8">
      {/* Profile Information */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Profile Information</h3>
        
        <div className="space-y-2">
          <Label htmlFor="name">Name</Label>
          <Input
            id="name"
            value={profile.name}
            onChange={(e) => {
              setProfile({ ...profile, name: e.target.value });
              onChange?.();
            }}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            value={profile.email}
            onChange={(e) => {
              setProfile({ ...profile, email: e.target.value });
              onChange?.();
            }}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="role">Role</Label>
          <Input
            id="role"
            value={profile.role}
            disabled
          />
        </div>

        <Button onClick={handleSaveProfile}>Save Profile</Button>
      </div>

      <Separator />

      {/* Change Password */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Change Password</h3>
        
        <div className="space-y-2">
          <Label htmlFor="currentPassword">Current Password</Label>
          <Input
            id="currentPassword"
            type="password"
            value={passwordForm.currentPassword}
            onChange={(e) => {
              setPasswordForm({ ...passwordForm, currentPassword: e.target.value });
              onChange?.();
            }}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="newPassword">New Password</Label>
          <Input
            id="newPassword"
            type="password"
            value={passwordForm.newPassword}
            onChange={(e) => {
              setPasswordForm({ ...passwordForm, newPassword: e.target.value });
              onChange?.();
            }}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="confirmPassword">Confirm New Password</Label>
          <Input
            id="confirmPassword"
            type="password"
            value={passwordForm.confirmPassword}
            onChange={(e) => {
              setPasswordForm({ ...passwordForm, confirmPassword: e.target.value });
              onChange?.();
            }}
          />
        </div>

        <Button onClick={handleChangePassword}>Change Password</Button>
      </div>
    </div>
  );
};

export default ProfileSettings;
