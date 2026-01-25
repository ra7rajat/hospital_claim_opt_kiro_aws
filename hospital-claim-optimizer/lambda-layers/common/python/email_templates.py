"""
Email Templates

Professional, mobile-responsive email templates for all notification types.

Requirements: 6.3.1, 6.3.2, 6.3.3, 6.3.4, 6.3.5
"""

from typing import Dict, Any


class EmailTemplates:
    """Email template renderer with support for dynamic content"""
    
    # Base HTML template with branding and responsive design
    BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{{subject}}</title>
    <style>
        /* Reset styles */
        body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
        table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
        img {{ -ms-interpolation-mode: bicubic; border: 0; height: auto; line-height: 100%; outline: none; text-decoration: none; }}
        
        /* Base styles */
        body {{
            margin: 0;
            padding: 0;
            width: 100% !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f3f4f6;
        }}
        
        /* Container */
        .email-container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            padding: 30px 20px;
            text-align: center;
        }}
        
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #ffffff;
            text-decoration: none;
        }}
        
        /* Content */
        .content {{
            padding: 40px 30px;
            color: #1f2937;
            line-height: 1.6;
        }}
        
        .content h1 {{
            font-size: 24px;
            font-weight: 600;
            margin: 0 0 20px 0;
            color: #111827;
        }}
        
        .content p {{
            margin: 0 0 15px 0;
            font-size: 16px;
        }}
        
        /* Button */
        .button {{
            display: inline-block;
            padding: 14px 28px;
            margin: 20px 0;
            background-color: #3b82f6;
            color: #ffffff !important;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 16px;
        }}
        
        .button:hover {{
            background-color: #2563eb;
        }}
        
        /* Info box */
        .info-box {{
            background-color: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 16px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        .warning-box {{
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 16px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        .success-box {{
            background-color: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 16px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        /* Table */
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        .data-table th {{
            background-color: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #e5e7eb;
        }}
        
        .data-table td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        /* Footer */
        .footer {{
            background-color: #f9fafb;
            padding: 30px 20px;
            text-align: center;
            font-size: 14px;
            color: #6b7280;
            border-top: 1px solid #e5e7eb;
        }}
        
        .footer a {{
            color: #3b82f6;
            text-decoration: none;
        }}
        
        .footer a:hover {{
            text-decoration: underline;
        }}
        
        /* Mobile responsive */
        @media only screen and (max-width: 600px) {{
            .content {{
                padding: 30px 20px !important;
            }}
            
            .content h1 {{
                font-size: 20px !important;
            }}
            
            .button {{
                display: block !important;
                width: 100% !important;
                text-align: center !important;
            }}
        }}
    </style>
</head>
<body>
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" class="email-container" cellspacing="0" cellpadding="0" border="0">
                    <!-- Header -->
                    <tr>
                        <td class="header">
                            <a href="{{app_url}}" class="logo">Hospital Claim Optimizer</a>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td class="content">
                            {{content}}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td class="footer">
                            <p>&copy; 2025 Hospital Claim Optimizer. All rights reserved.</p>
                            <p>
                                <a href="{{app_url}}">Visit Dashboard</a> | 
                                <a href="{{help_url}}">Help Center</a> | 
                                <a href="{{unsubscribe_url}}">Unsubscribe</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    # Alert notification template
    ALERT_TEMPLATE = """
<h1>⚠️ {{alert_title}}</h1>
<p>{{alert_message}}</p>

<div class="warning-box">
    <strong>Alert Details:</strong><br>
    <strong>Type:</strong> {{alert_type}}<br>
    <strong>Severity:</strong> {{severity}}<br>
    <strong>Time:</strong> {{timestamp}}
</div>

<p>{{action_required}}</p>

<a href="{{action_url}}" class="button">View Alert Details</a>

<p style="color: #6b7280; font-size: 14px;">
    This is an automated alert from your Hospital Claim Optimizer system.
</p>
"""
    
    # Report notification template
    REPORT_TEMPLATE = """
<h1>📊 {{report_title}}</h1>
<p>Your {{report_type}} report is ready.</p>

<div class="info-box">
    <strong>Report Summary:</strong><br>
    {{report_summary}}
</div>

<table class="data-table">
    <thead>
        <tr>
            <th>Metric</th>
            <th>Value</th>
        </tr>
    </thead>
    <tbody>
        {{metrics_rows}}
    </tbody>
</table>

<a href="{{report_url}}" class="button">View Full Report</a>

<p style="color: #6b7280; font-size: 14px;">
    Report generated on {{generation_date}}
</p>
"""
    
    # Policy update notification template
    POLICY_UPDATE_TEMPLATE = """
<h1>📋 Policy Update: {{policy_name}}</h1>
<p>A policy has been {{action}} in your system.</p>

<div class="info-box">
    <strong>Policy Details:</strong><br>
    <strong>Policy Name:</strong> {{policy_name}}<br>
    <strong>Policy ID:</strong> {{policy_id}}<br>
    <strong>Version:</strong> {{version}}<br>
    <strong>Updated By:</strong> {{updated_by}}<br>
    <strong>Date:</strong> {{update_date}}
</div>

{{change_summary}}

<a href="{{policy_url}}" class="button">View Policy Details</a>

<p style="color: #6b7280; font-size: 14px;">
    {{affected_claims_message}}
</p>
"""
    
    # Claim status notification template
    CLAIM_STATUS_TEMPLATE = """
<h1>{{status_icon}} Claim Status Update</h1>
<p>The status of claim <strong>#{{claim_id}}</strong> has been updated.</p>

<div class="{{status_box_class}}">
    <strong>New Status:</strong> {{new_status}}<br>
    <strong>Previous Status:</strong> {{previous_status}}<br>
    <strong>Updated:</strong> {{update_time}}
</div>

<table class="data-table">
    <thead>
        <tr>
            <th>Detail</th>
            <th>Value</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Patient</td>
            <td>{{patient_name}}</td>
        </tr>
        <tr>
            <td>Procedure</td>
            <td>{{procedure_name}}</td>
        </tr>
        <tr>
            <td>Claim Amount</td>
            <td>{{claim_amount}}</td>
        </tr>
        <tr>
            <td>Settlement Ratio</td>
            <td>{{settlement_ratio}}</td>
        </tr>
    </tbody>
</table>

{{status_message}}

<a href="{{claim_url}}" class="button">View Claim Details</a>
"""
    
    # Daily digest template
    DAILY_DIGEST_TEMPLATE = """
<h1>📅 Daily Summary - {{date}}</h1>
<p>Here's your daily summary of activity in the Hospital Claim Optimizer.</p>

<div class="info-box">
    <strong>Today's Highlights:</strong><br>
    • {{total_claims}} claims processed<br>
    • {{alerts_count}} new alerts<br>
    • {{policies_updated}} policies updated<br>
    • Average settlement ratio: {{avg_settlement_ratio}}%
</div>

<h2 style="font-size: 18px; margin-top: 30px;">Recent Alerts</h2>
{{alerts_section}}

<h2 style="font-size: 18px; margin-top: 30px;">Claim Updates</h2>
{{claims_section}}

<h2 style="font-size: 18px; margin-top: 30px;">Policy Changes</h2>
{{policies_section}}

<a href="{{dashboard_url}}" class="button">View Dashboard</a>

<p style="color: #6b7280; font-size: 14px;">
    You're receiving this daily digest because of your notification preferences.
    <a href="{{preferences_url}}">Update preferences</a>
</p>
"""
    
    # Weekly digest template
    WEEKLY_DIGEST_TEMPLATE = """
<h1>📈 Weekly Summary - Week of {{week_start}}</h1>
<p>Here's your weekly summary of activity in the Hospital Claim Optimizer.</p>

<div class="success-box">
    <strong>This Week's Performance:</strong><br>
    • {{total_claims}} total claims<br>
    • {{approved_claims}} approved claims<br>
    • {{avg_settlement_ratio}}% average settlement ratio<br>
    • {{cost_savings}} in optimized savings
</div>

<h2 style="font-size: 18px; margin-top: 30px;">Key Metrics</h2>
<table class="data-table">
    <thead>
        <tr>
            <th>Metric</th>
            <th>This Week</th>
            <th>Last Week</th>
            <th>Change</th>
        </tr>
    </thead>
    <tbody>
        {{metrics_comparison}}
    </tbody>
</table>

<h2 style="font-size: 18px; margin-top: 30px;">Top Alerts</h2>
{{top_alerts}}

<h2 style="font-size: 18px; margin-top: 30px;">Policy Activity</h2>
{{policy_activity}}

<a href="{{reports_url}}" class="button">View Detailed Reports</a>

<p style="color: #6b7280; font-size: 14px;">
    You're receiving this weekly digest because of your notification preferences.
    <a href="{{preferences_url}}">Update preferences</a>
</p>
"""
    
    # Welcome email template
    WELCOME_TEMPLATE = """
<h1>👋 Welcome to Hospital Claim Optimizer!</h1>
<p>Hi {{user_name}},</p>

<p>We're excited to have you on board! Your account has been successfully created and you're ready to start optimizing your hospital insurance claim settlements.</p>

<div class="success-box">
    <strong>Your Account Details:</strong><br>
    <strong>Email:</strong> {{user_email}}<br>
    <strong>Role:</strong> {{user_role}}<br>
    <strong>Organization:</strong> {{organization}}
</div>

<h2 style="font-size: 18px; margin-top: 30px;">Getting Started</h2>
<p>Here are some quick steps to get you started:</p>
<ol>
    <li>Complete your profile setup</li>
    <li>Upload your first insurance policy</li>
    <li>Run an eligibility check</li>
    <li>Explore the dashboard and reports</li>
</ol>

<a href="{{dashboard_url}}" class="button">Go to Dashboard</a>

<p style="margin-top: 30px;">Need help? Check out our <a href="{{help_url}}">Help Center</a> or contact support.</p>
"""
    
    @classmethod
    def render_template(
        cls,
        template_type: str,
        data: Dict[str, Any],
        app_url: str = "https://app.hospital-claim-optimizer.com",
        help_url: str = "https://help.hospital-claim-optimizer.com",
        unsubscribe_url: str = ""
    ) -> tuple[str, str]:
        """
        Render an email template with data
        
        Args:
            template_type: Type of template (alert, report, policy_update, claim_status, daily_digest, weekly_digest, welcome)
            data: Dict with template data
            app_url: Application URL
            help_url: Help center URL
            unsubscribe_url: Unsubscribe URL
        
        Returns:
            Tuple of (html_body, text_body)
        
        Requirements: 6.3.1, 6.3.2, 6.3.3, 6.3.4
        """
        # Get template content
        template_map = {
            'alert': cls.ALERT_TEMPLATE,
            'report': cls.REPORT_TEMPLATE,
            'policy_update': cls.POLICY_UPDATE_TEMPLATE,
            'claim_status': cls.CLAIM_STATUS_TEMPLATE,
            'daily_digest': cls.DAILY_DIGEST_TEMPLATE,
            'weekly_digest': cls.WEEKLY_DIGEST_TEMPLATE,
            'welcome': cls.WELCOME_TEMPLATE
        }
        
        content_template = template_map.get(template_type, '')
        if not content_template:
            raise ValueError(f"Unknown template type: {template_type}")
        
        # Render content with data
        content = cls._replace_placeholders(content_template, data)
        
        # Render full HTML with base template
        html_data = {
            'subject': data.get('subject', 'Notification'),
            'content': content,
            'app_url': app_url,
            'help_url': help_url,
            'unsubscribe_url': unsubscribe_url
        }
        html_body = cls._replace_placeholders(cls.BASE_TEMPLATE, html_data)
        
        # Generate plain text version
        text_body = cls._html_to_text(content, data)
        
        return html_body, text_body
    
    @classmethod
    def _replace_placeholders(cls, template: str, data: Dict[str, Any]) -> str:
        """Replace {{placeholder}} with data values"""
        result = template
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    @classmethod
    def _html_to_text(cls, html_content: str, data: Dict[str, Any]) -> str:
        """Convert HTML content to plain text"""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Replace multiple spaces/newlines with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Add data values
        text = cls._replace_placeholders(text, data)
        
        # Clean up
        text = text.strip()
        
        return text


# Helper functions for common template patterns

def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.1f}%"


def format_date(date_str: str) -> str:
    """Format date string"""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except:
        return date_str


def get_status_icon(status: str) -> str:
    """Get emoji icon for status"""
    icons = {
        'approved': '✅',
        'rejected': '❌',
        'pending': '⏳',
        'processing': '🔄',
        'completed': '✅',
        'failed': '❌'
    }
    return icons.get(status.lower(), '📋')


def get_status_box_class(status: str) -> str:
    """Get CSS class for status box"""
    if status.lower() in ['approved', 'completed']:
        return 'success-box'
    elif status.lower() in ['rejected', 'failed']:
        return 'warning-box'
    else:
        return 'info-box'
