/**
 * Webhook Settings Component
 * Manages webhook configurations
 * Requirements: 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.2.5, 3.3.1, 3.3.2, 3.3.3, 3.3.4, 3.3.5, 3.4.1, 3.4.2, 3.4.3, 3.4.4, 3.4.5
 */
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Trash2, Edit, TestTube, Activity, CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';

interface Webhook {
  webhook_id: string;
  name: string;
  url: string;
  description: string;
  enabled: boolean;
  events: string[];
  auth_type: 'api_key' | 'oauth2';
  auth_config: {
    api_key?: string;
    client_id?: string;
    client_secret?: string;
    token_url?: string;
  };
  created_at: string;
  updated_at: string;
}

interface WebhookDelivery {
  delivery_id: string;
  event_type: string;
  status: 'success' | 'failed';
  status_code?: number;
  response_time_ms: number;
  timestamp: string;
  error?: string;
}

interface WebhookSettingsProps {
  onUpdate?: () => void;
  onChange?: () => void;
}

const AVAILABLE_EVENTS = [
  { value: 'claim_submitted', label: 'Claim Submitted' },
  { value: 'claim_approved', label: 'Claim Approved' },
  { value: 'claim_rejected', label: 'Claim Rejected' },
  { value: 'audit_completed', label: 'Audit Completed' },
  { value: 'high_risk_detected', label: 'High Risk Detected' },
  { value: 'policy_updated', label: 'Policy Updated' },
  { value: 'policy_expired', label: 'Policy Expired' },
  { value: 'settlement_completed', label: 'Settlement Completed' },
];

const WebhookSettings: React.FC<WebhookSettingsProps> = ({ onUpdate, onChange }) => {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [selectedWebhook, setSelectedWebhook] = useState<Webhook | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isTestDialogOpen, setIsTestDialogOpen] = useState(false);
  const [isActivityDialogOpen, setIsActivityDialogOpen] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    description: '',
    enabled: true,
    events: [] as string[],
    auth_type: 'api_key' as 'api_key' | 'oauth2',
    api_key: '',
    client_id: '',
    client_secret: '',
    token_url: '',
  });

  useEffect(() => {
    loadWebhooks();
  }, []);

  const loadWebhooks = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/webhooks', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setWebhooks(data.webhooks || []);
      }
    } catch (err) {
      setError('Failed to load webhooks');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWebhook = () => {
    setSelectedWebhook(null);
    setFormData({
      name: '',
      url: '',
      description: '',
      enabled: true,
      events: [],
      auth_type: 'api_key',
      api_key: '',
      client_id: '',
      client_secret: '',
      token_url: '',
    });
    setIsDialogOpen(true);
  };

  const handleEditWebhook = (webhook: Webhook) => {
    setSelectedWebhook(webhook);
    setFormData({
      name: webhook.name,
      url: webhook.url,
      description: webhook.description,
      enabled: webhook.enabled,
      events: webhook.events,
      auth_type: webhook.auth_type,
      api_key: webhook.auth_config.api_key || '',
      client_id: webhook.auth_config.client_id || '',
      client_secret: webhook.auth_config.client_secret || '',
      token_url: webhook.auth_config.token_url || '',
    });
    setIsDialogOpen(true);
  };

  const handleSaveWebhook = async () => {
    try {
      setLoading(true);
      setError(null);

      const payload = {
        name: formData.name,
        url: formData.url,
        description: formData.description,
        enabled: formData.enabled,
        events: formData.events,
        auth_type: formData.auth_type,
        auth_config: formData.auth_type === 'api_key'
          ? { api_key: formData.api_key }
          : {
              client_id: formData.client_id,
              client_secret: formData.client_secret,
              token_url: formData.token_url,
            },
      };

      const url = selectedWebhook
        ? `/api/webhooks/${selectedWebhook.webhook_id}`
        : '/api/webhooks';
      
      const method = selectedWebhook ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        await loadWebhooks();
        setIsDialogOpen(false);
        onUpdate?.();
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to save webhook');
      }
    } catch (err) {
      setError('Failed to save webhook');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWebhook = async (webhookId: string) => {
    if (!confirm('Are you sure you want to delete this webhook?')) {
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`/api/webhooks/${webhookId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        await loadWebhooks();
        onUpdate?.();
      }
    } catch (err) {
      setError('Failed to delete webhook');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleWebhook = async (webhookId: string, enabled: boolean) => {
    try {
      const response = await fetch(`/api/webhooks/${webhookId}/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ enabled }),
      });

      if (response.ok) {
        await loadWebhooks();
        onChange?.();
      }
    } catch (err) {
      setError('Failed to toggle webhook');
    }
  };

  const handleTestWebhook = async (webhook: Webhook) => {
    setSelectedWebhook(webhook);
    setTestResult(null);
    setIsTestDialogOpen(true);

    try {
      setLoading(true);
      const response = await fetch('/api/webhooks/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          url: webhook.url,
          event_type: 'test_event',
          auth_type: webhook.auth_type,
          auth_config: webhook.auth_config,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setTestResult(result);
      }
    } catch (err) {
      setTestResult({ success: false, error: 'Test failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleViewActivity = async (webhook: Webhook) => {
    setSelectedWebhook(webhook);
    setIsActivityDialogOpen(true);

    try {
      setLoading(true);
      const response = await fetch(`/api/webhooks/${webhook.webhook_id}/activity`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDeliveries(data.deliveries || []);
      }
    } catch (err) {
      setError('Failed to load activity');
    } finally {
      setLoading(false);
    }
  };

  const handleRetryDelivery = async (deliveryId: string) => {
    if (!selectedWebhook) return;

    try {
      const response = await fetch(`/api/webhooks/${selectedWebhook.webhook_id}/retry/${deliveryId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        await handleViewActivity(selectedWebhook);
      }
    } catch (err) {
      setError('Failed to retry delivery');
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Webhook List */}
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold">Configured Webhooks</h3>
          <Button onClick={handleCreateWebhook}>
            <Plus className="h-4 w-4 mr-2" />
            Add Webhook
          </Button>
        </div>

        {webhooks.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed rounded-lg">
            <p className="text-muted-foreground">No webhooks configured</p>
            <Button variant="link" onClick={handleCreateWebhook}>
              Create your first webhook
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {webhooks.map((webhook) => (
              <div
                key={webhook.webhook_id}
                className="border rounded-lg p-4 space-y-3"
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-semibold">{webhook.name}</h4>
                      <Badge variant={webhook.enabled ? 'default' : 'secondary'}>
                        {webhook.enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{webhook.url}</p>
                    {webhook.description && (
                      <p className="text-sm">{webhook.description}</p>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <Switch
                      checked={webhook.enabled}
                      onCheckedChange={(checked) => handleToggleWebhook(webhook.webhook_id, checked)}
                    />
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {webhook.events.map((event) => (
                    <Badge key={event} variant="outline">
                      {AVAILABLE_EVENTS.find((e) => e.value === event)?.label || event}
                    </Badge>
                  ))}
                </div>

                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEditWebhook(webhook)}
                  >
                    <Edit className="h-4 w-4 mr-1" />
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTestWebhook(webhook)}
                  >
                    <TestTube className="h-4 w-4 mr-1" />
                    Test
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleViewActivity(webhook)}
                  >
                    <Activity className="h-4 w-4 mr-1" />
                    Activity
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeleteWebhook(webhook.webhook_id)}
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedWebhook ? 'Edit Webhook' : 'Create Webhook'}
            </DialogTitle>
            <DialogDescription>
              Configure webhook to receive real-time notifications
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => {
                  setFormData({ ...formData, name: e.target.value });
                  onChange?.();
                }}
                placeholder="Production Webhook"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="url">URL *</Label>
              <Input
                id="url"
                type="url"
                value={formData.url}
                onChange={(e) => {
                  setFormData({ ...formData, url: e.target.value });
                  onChange?.();
                }}
                placeholder="https://example.com/webhook"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => {
                  setFormData({ ...formData, description: e.target.value });
                  onChange?.();
                }}
                placeholder="Webhook for production environment"
              />
            </div>

            <div className="space-y-2">
              <Label>Events *</Label>
              <div className="grid grid-cols-2 gap-2">
                {AVAILABLE_EVENTS.map((event) => (
                  <label key={event.value} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.events.includes(event.value)}
                      onChange={(e) => {
                        const newEvents = e.target.checked
                          ? [...formData.events, event.value]
                          : formData.events.filter((ev) => ev !== event.value);
                        setFormData({ ...formData, events: newEvents });
                        onChange?.();
                      }}
                    />
                    <span className="text-sm">{event.label}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="auth_type">Authentication Type</Label>
              <Select
                value={formData.auth_type}
                onValueChange={(value: 'api_key' | 'oauth2') => {
                  setFormData({ ...formData, auth_type: value });
                  onChange?.();
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="api_key">API Key</SelectItem>
                  <SelectItem value="oauth2">OAuth 2.0</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {formData.auth_type === 'api_key' ? (
              <div className="space-y-2">
                <Label htmlFor="api_key">API Key</Label>
                <Input
                  id="api_key"
                  type="password"
                  value={formData.api_key}
                  onChange={(e) => {
                    setFormData({ ...formData, api_key: e.target.value });
                    onChange?.();
                  }}
                  placeholder="Enter API key"
                />
              </div>
            ) : (
              <>
                <div className="space-y-2">
                  <Label htmlFor="client_id">Client ID</Label>
                  <Input
                    id="client_id"
                    value={formData.client_id}
                    onChange={(e) => {
                      setFormData({ ...formData, client_id: e.target.value });
                      onChange?.();
                    }}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="client_secret">Client Secret</Label>
                  <Input
                    id="client_secret"
                    type="password"
                    value={formData.client_secret}
                    onChange={(e) => {
                      setFormData({ ...formData, client_secret: e.target.value });
                      onChange?.();
                    }}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="token_url">Token URL</Label>
                  <Input
                    id="token_url"
                    type="url"
                    value={formData.token_url}
                    onChange={(e) => {
                      setFormData({ ...formData, token_url: e.target.value });
                      onChange?.();
                    }}
                    placeholder="https://auth.example.com/token"
                  />
                </div>
              </>
            )}

            <div className="flex items-center space-x-2">
              <Switch
                id="enabled"
                checked={formData.enabled}
                onCheckedChange={(checked) => {
                  setFormData({ ...formData, enabled: checked });
                  onChange?.();
                }}
              />
              <Label htmlFor="enabled">Enable webhook</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveWebhook} disabled={loading}>
              {loading ? 'Saving...' : 'Save Webhook'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Test Dialog */}
      <Dialog open={isTestDialogOpen} onOpenChange={setIsTestDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Test Webhook</DialogTitle>
            <DialogDescription>
              Testing: {selectedWebhook?.name}
            </DialogDescription>
          </DialogHeader>

          {loading ? (
            <div className="py-8 text-center">
              <p>Testing webhook...</p>
            </div>
          ) : testResult ? (
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                {testResult.success ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-500" />
                )}
                <span className="font-semibold">
                  {testResult.success ? 'Test Successful' : 'Test Failed'}
                </span>
              </div>

              {testResult.status_code && (
                <div>
                  <Label>Status Code</Label>
                  <p>{testResult.status_code}</p>
                </div>
              )}

              {testResult.response_time_ms && (
                <div>
                  <Label>Response Time</Label>
                  <p>{testResult.response_time_ms}ms</p>
                </div>
              )}

              {testResult.error && (
                <div>
                  <Label>Error</Label>
                  <p className="text-red-500">{testResult.error}</p>
                </div>
              )}

              {testResult.response_body && (
                <div>
                  <Label>Response</Label>
                  <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-40">
                    {testResult.response_body}
                  </pre>
                </div>
              )}
            </div>
          ) : null}

          <DialogFooter>
            <Button onClick={() => setIsTestDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Activity Dialog */}
      <Dialog open={isActivityDialogOpen} onOpenChange={setIsActivityDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>Webhook Activity</DialogTitle>
            <DialogDescription>
              Delivery logs for: {selectedWebhook?.name}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 overflow-y-auto max-h-[60vh]">
            {deliveries.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                No deliveries yet
              </p>
            ) : (
              deliveries.map((delivery) => (
                <div
                  key={delivery.delivery_id}
                  className="border rounded-lg p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {delivery.status === 'success' ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                      )}
                      <span className="font-semibold">{delivery.event_type}</span>
                      <Badge variant={delivery.status === 'success' ? 'default' : 'destructive'}>
                        {delivery.status}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      <span>{new Date(delivery.timestamp).toLocaleString()}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    {delivery.status_code && (
                      <div>
                        <Label>Status Code</Label>
                        <p>{delivery.status_code}</p>
                      </div>
                    )}
                    <div>
                      <Label>Response Time</Label>
                      <p>{delivery.response_time_ms}ms</p>
                    </div>
                  </div>

                  {delivery.error && (
                    <div>
                      <Label>Error</Label>
                      <p className="text-red-500 text-sm">{delivery.error}</p>
                    </div>
                  )}

                  {delivery.status === 'failed' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRetryDelivery(delivery.delivery_id)}
                    >
                      Retry
                    </Button>
                  )}
                </div>
              ))
            )}
          </div>

          <DialogFooter>
            <Button onClick={() => setIsActivityDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default WebhookSettings;
