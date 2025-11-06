# Azure Function Webhook Service - Wiz GitHub Findings to Azure DevOps

This project creates an Azure Function that receives Wiz vulnerability findings from **GitHub repositories** via webhook and automatically creates Issue work items in Azure DevOps.

## 🎯 Focus: GitHub Repository Vulnerabilities

This integration is specifically designed to handle vulnerability findings from GitHub repositories detected by Wiz. When Wiz identifies vulnerabilities in your GitHub code repositories, this webhook automatically creates trackable work items in Azure DevOps for remediation.

## Architecture

- **Azure Function App**: Linux-based serverless function (Python 3.11)
- **Storage Account**: Required for Azure Functions runtime
- **Application Insights**: For monitoring and logging
- **App Service Plan**: Consumption (serverless) plan
- **Azure DevOps Integration**: Automatically creates User Story work items

## Features

- ✅ Receives Wiz vulnerability findings from **GitHub repositories**
- ✅ Automatically creates Azure DevOps User Story work items
- ✅ Formats work item title as: "Wiz Vuln Findings - {issue.name}"
- ✅ Rich HTML description with:
  - Issue summary and severity
  - GitHub repository details and direct link
  - Remediation instructions from Wiz
  - Link to Wiz platform for full details
  - Policy and trigger information
- ✅ Maps Wiz severity to Azure DevOps priority (HIGH→2, MEDIUM→3, etc.)
- ✅ Tags work items with: Wiz, Vulnerability, Security, GitHub, Severity, Repository name
- ✅ Adds acceptance criteria with remediation steps
- ✅ Comprehensive logging and error handling

## Files Structure

```
.
├── main.tf                 # Terraform infrastructure code
├── function_app.py         # Python function code with Azure DevOps integration
├── requirements.txt        # Python dependencies
├── host.json              # Function app configuration
├── terraform.tfvars.example # Example configuration file
├── .gitignore             # Git ignore patterns
├── deploy.sh              # Deployment script
└── README.md              # This file
```

## Prerequisites

- Azure CLI installed and configured (`az login`)
- Terraform installed (>= 1.0)
- Azure DevOps organization and project

## Setup Instructions

### 1. Configure Terraform Variables

Copy the example configuration file:
```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your Azure DevOps details:
```hcl
azdo_org_url = "https://dev.azure.com/yourcompany"
azdo_project = "YourProjectName"
```

⚠️ **IMPORTANT**: Never commit `terraform.tfvars` to version control! It's already in `.gitignore`.

### 3. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply
```

### 4. Deploy Function Code

**Option A: Using Azure Functions Core Tools (Recommended)**
```bash
func azure functionapp publish <function_app_name>
```

**Option B: Using the deployment script**
```bash
./deploy.sh
```

**Option C: Using Azure CLI**
```bash
zip -r function.zip function_app.py requirements.txt host.json .funcignore
az functionapp deployment source config-zip \
  --resource-group rg-webhook-function \
  --name <function_app_name> \
  --src function.zip
```

## Wiz Webhook Configuration

### Expected Payload Structure

The function expects a JSON payload from Wiz with the following structure for **GitHub repository findings**:

```json
{
  "trigger": {
    "type": "Manually Triggered",
    "ruleName": "Manual"
  },
  "issue": {
    "id": "cb0ac949-af1d-4019-92fa-d2c45acb34e6",
    "status": "OPEN",
    "severity": "HIGH",
    "created": "2025-11-01T02:16:58.492358Z",
    "name": "Critical Vulnerability in TensorFlow",
    "description": "The resource has a critical vulnerability... It can be resolved by upgrading...",
    "entitySnapshot": "<org>/<repo>/main",
    "refLink": "https://app.wiz.io/issues#~..."
  },
  "resource": {
    "name": "<org>/<repo>/main/main",
    "type": "github#repositoryBranch",
    "cloudPlatform": "GitHub",
    "cloudProviderURL": "https://github.com/<org>/<repo>/main/tree/main"
  },
  "policy": {
    "id": "5e30b85d-39dc-4baa-af52-b740bd87a919",
    "name": "GitHub Vulnerability Policy"
  }
}
```

### Configure Wiz to Send Webhooks

1. Log into Wiz platform
2. Go to **Settings → Integrations**
3. Create a new Integration of type Webhook:
   - **Name**: ADO Manual Integration
   - **URL**: `https://<your-function-app>.azurewebsites.net/api/webhook`
4. Test the webhook with a manual trigger
5. Save the configuration

## Testing the Integration

### Test with curl

```bash
curl -X POST https://<your-function-app>.azurewebsites.net/api/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "issue": {
      "name": "Test Vulnerability Finding",
      "severity": "HIGH",
      "description": "This is a test vulnerability",
      "status": "OPEN"
    }
  }'
```

### Expected Response

**For Findings (Success):**
```json
{
  "status": "success",
  "message": "Azure DevOps work item created successfully for GitHub finding",
  "work_item": {
    "work_item_id": 12345,
    "work_item_url": "https://dev.azure.com/yourorg/yourproject/_workitems/edit/12345",
    "title": "Wiz Vuln Findings - Critical Vulnerability in TensorFlow",
    "repository": "<org>/<repo>/main/main",
    "severity": "HIGH"
  },
  "received_issue": "Critical Vulnerability in TensorFlow",
  "repository": "<org>/<repo>/main/main"
}
```


### Verify in Azure DevOps

1. Go to your Azure DevOps project
2. Navigate to **Boards → Work Items**
3. You should see a new User Story with:
   - **Title**: "Wiz Vuln Findings - {issue name}"
   - **Description**: Rich HTML formatted with:
     - Issue summary table (name, status, severity, created date)
     - Detailed vulnerability description with remediation steps
     - GitHub repository details with clickable link
     - Direct link to Wiz platform issue
     - Policy information
     - Trigger information
     - Collapsible raw JSON payload
   - **Tags**: Wiz, Vulnerability, Security, GitHub, Severity-HIGH, Repo-{reponame}
   - **Priority**: Based on severity (Critical=1, High=2, Medium=3, Low=4)
   - **Acceptance Criteria**: Includes remediation steps and verification checklist

### Work Item Example

For the sample GitHub finding, the work item would have:

- **Title**: "Wiz Vuln Findings - Critical Vulnerability in TensorFlow"
- **Priority**: 2 (HIGH)
- **Tags**: Wiz; Vulnerability; Security; GitHub; Severity-HIGH; Repo-wiz-code-gha
- **Description**: Formatted HTML showing:
  - Repository: ` <org>/<repo>/main/main`
  - GitHub URL: Link to the repository/branch
  - Remediation: "Upgrade tensorflow to 2.14.1"
  - Wiz Link: Direct link to issue in Wiz platform

## Severity to Priority Mapping

| Wiz Severity | Azure DevOps Priority |
|--------------|----------------------|
| CRITICAL     | 1                    |
| HIGH         | 2                    |
| MEDIUM       | 3                    |
| LOW          | 4                    |

## Viewing Logs

### Azure Portal
1. Navigate to your Function App
2. Go to "Functions" → "webhook"
3. Click "Monitor" or go to Application Insights

### Azure CLI
```bash
az functionapp log tail \
  --name <function_app_name> \
  --resource-group rg-webhook-function
```

### Azure Functions Core Tools
```bash
func azure functionapp logstream <function_app_name>
```

## Troubleshooting

### Work Item Creation Fails

**Error**: Missing Azure DevOps configuration
- **Solution**: Verify environment variables are set correctly in Function App settings
- Check: AZDO_ORG_URL, AZDO_PAT, AZDO_PROJECT

**Error**: 401 Unauthorized
- **Solution**: Verify PAT token has correct permissions (Work Items: Read, Write & Manage)
- Check if PAT token has expired

**Error**: Project not found
- **Solution**: Verify project name is correct (case-sensitive)

### Function Not Responding

- Check if function app is running in Azure Portal
- Verify deployment was successful
- Check Application Insights logs for errors

### Webhook Payload Issues

- Ensure payload contains `issue` field at root level
- Verify JSON is properly formatted
- Check function logs for parsing errors

### Recommended Production Security

1. **Enable Function Keys**:
   ```python
   @app.route(route="webhook", auth_level=func.AuthLevel.FUNCTION, methods=["POST"])
   ```

2. **IP Restrictions**: Configure in Azure Portal → Networking

3. **Azure Key Vault**: Store PAT in Key Vault and reference it

## Customization

### Modify Work Item Type

Change from Issue to Bug or Task:

```python
work_item = wit_client.create_work_item(
    document=document,
    project=project_name,
    type='Bug'  # or 'Task'
)
```

### Add Custom Fields

Add more fields to the work item:

```python
document.append({
    "op": "add",
    "path": "/fields/Custom.FieldName",
    "value": "Custom Value"
})
```

### Modify Description Format

Update the description formatting in `create_work_item()` function.

## Cost Estimation

### Azure Functions (Consumption Plan)
- First 1 million executions: Free
- After: $0.20 per million executions
- Execution time: $0.000016 per GB-second

### Typical Costs
- Low volume (< 10,000 webhooks/month): Free tier
- Medium volume (100,000 webhooks/month): ~$2-5/month
- High volume (1M webhooks/month): ~$20-30/month

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Note**: This will NOT delete work items already created in Azure DevOps.

## Support

For issues or questions:
1. Check Application Insights logs
2. Verify webhook payload format
4. Check function app environment variables

## License

This project is provided as-is for demonstration purposes.
