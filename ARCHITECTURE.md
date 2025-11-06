# Architecture - Wiz to Azure DevOps Integration

## System Overview

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────────┐
│             │         │                  │         │                 │
│     Wiz     │────────▶│  Azure Function  │────────▶│  Azure DevOps   │
│   Platform  │ Webhook │   (Python 3.11)  │   API   │   Work Items    │
│             │         │                  │         │                 │
└─────────────┘         └──────────────────┘         └─────────────────┘
                               │
                               │
                               ▼
                        ┌──────────────┐
                        │ Application  │
                        │   Insights   │
                        │   (Logging)  │
                        └──────────────┘
```

## Data Flow

### 1. Wiz Detection
```
Wiz Platform detects a vulnerability finding
    ↓
Wiz formats the finding as JSON
    ↓
Wiz sends HTTP POST to webhook URL
```

### 2. Azure Function Processing
```
Azure Function receives POST request
    ↓
Validates JSON structure (must have "issue" field)
    ↓
Extracts issue information:
    - issue.name → Work item title
    - issue.severity → Priority mapping
    - Full payload → Description
    ↓
Logs the payload to Application Insights
    ↓
Calls Azure DevOps REST API
```

### 3. Azure DevOps Work Item Creation
```
Azure DevOps API receives request
    ↓
Authenticates with Managed Identity
    ↓
Creates User Story work item:
    - Title: "Wiz Vuln Findings - {issue.name}"
    - Description: Full JSON payload
    - Priority: Based on severity
    - Tags: Wiz, Vulnerability, Security
    ↓
Returns work item ID and URL
```

### 4. Response
```
Function returns success response to Wiz:
    {
      "status": "success",
      "work_item": {
        "work_item_id": 12345,
        "work_item_url": "..."
      }
    }
```

## Component Details

### Azure Function App
- **Runtime**: Python 3.11
- **Plan**: Consumption (Serverless)
- **Trigger**: HTTP POST
- **Authentication**: Anonymous (configurable)
- **Region**: Central US (configurable)

### Dependencies
- `azure-functions`: Azure Functions SDK
- `azure-devops`: Azure DevOps REST API client

### Environment Variables
- `AZDO_ORG_URL`: Azure DevOps organization URL
- `AZDO_PROJECT`: Target project name
- `APPINSIGHTS_INSTRUMENTATIONKEY`: Application Insights key

### Security Model
```
┌──────────────────────────────────────┐
│ Network Layer                        │
│  ├─ HTTPS Only                       │
│  ├─ Optional: IP Restrictions        │
│  └─ Optional: Function Key Auth      │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ Application Layer                    │
│  ├─ Input Validation                 │
│  ├─ JSON Schema Validation           │
│  └─ Error Handling                   │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ Integration Layer                    │
│  ├─ Project-level Permissions        │
│  └─ Work Item API Access             │
└──────────────────────────────────────┘
```

## Severity to Priority Mapping

```
Wiz Severity          Azure DevOps Priority
─────────────────────────────────────────
CRITICAL        ───▶        1
HIGH            ───▶        2
MEDIUM          ───▶        3
LOW             ───▶        4
```

## Error Handling

### Validation Errors (HTTP 400)
- Missing "issue" field in JSON
- Invalid JSON format
- Malformed payload

### Configuration Errors (HTTP 500)
- Missing Azure DevOps environment variables
- Project not found

### API Errors (HTTP 500)
- Azure DevOps API unavailable
- Authentication failures
- Permission issues

## Monitoring and Logging

### Application Insights Tracks:
1. **Requests**: Every webhook call
2. **Dependencies**: Azure DevOps API calls
3. **Exceptions**: All errors and failures
4. **Custom Events**: Work item creation events
5. **Traces**: Detailed execution logs

### Log Levels:
- `INFO`: Normal operations, received payloads
- `WARNING`: Non-critical issues
- `ERROR`: Failed operations, API errors

## Infrastructure Components

### Resource Group: `rg-webhook-function`
Contains all resources for the integration

### Storage Account: `stwebhookfunc{random}`
Required by Azure Functions runtime

### App Service Plan: `asp-webhook-function`
Consumption plan (pay-per-execution)

### Function App: `func-webhook-{random}`
The actual function application

### Application Insights: `appi-webhook-function`
Monitoring and diagnostics

## Scalability

### Automatic Scaling
- Consumption plan scales automatically
- Up to 200 instances per function app
- No manual scaling configuration needed

### Performance
- Cold start: ~1-3 seconds
- Warm execution: <500ms
- Concurrent executions: Unlimited (within quota)

### Limits
- Function timeout: 5 minutes (default)
- Maximum payload size: 100 MB
- Concurrent executions: 200 per region

## Cost Breakdown

### Azure Function (Consumption)
- Executions: $0.20 per million (first 1M free)
- Execution time: $0.000016 per GB-second
- Memory: 256 MB default

### Storage Account
- ~$0.50-$1.00 per month
- Function metadata and logs

### Application Insights
- First 5 GB per month: Free
- Additional: $2.30 per GB

### Estimated Monthly Cost
- Low usage (<10K webhooks): **Free**
- Medium usage (100K webhooks): **~$3-5**
- High usage (1M webhooks): **~$25-30**

## Disaster Recovery

### Backup Strategy
- Infrastructure: Terraform state (stored in backend)
- Configuration: terraform.tfvars (backup separately)
- Code: Version control (Git)

### Recovery Steps
1. Restore Terraform state
2. Run `terraform apply`
3. Deploy function code
4. Verify environment variables
5. Test with sample payload

### High Availability
- Built-in: Azure Functions automatically handles:
  - Multiple availability zones
  - Automatic failover
  - Load balancing

## Security Best Practices

### ✅ Implemented
- HTTPS only connections
- PAT token marked as sensitive in Terraform
- Environment variable storage (not in code)
- Input validation and sanitization
- Comprehensive error handling

### 🔧 Recommended for Production
- Enable Function Key authentication
- Implement IP address restrictions
- Store PAT in Azure Key Vault
- Set up Azure AD authentication
- Enable advanced threat protection
- Configure network isolation (VNet)
- Implement rate limiting
- Set up alerts for failed authentications

## Maintenance

### Regular Tasks
- **Weekly**: Review Application Insights for errors
- **Monthly**: Check PAT token expiration
- **Quarterly**: Review and rotate PAT tokens
- **As needed**: Update function code for new Wiz fields

### Updates
- Azure Functions runtime: Automatic
- Python version: Manual (in main.tf)
- Dependencies: Update requirements.txt

## Integration Points

### Wiz Platform
- **Outbound**: HTTPS POST to webhook URL
- **Format**: JSON payload
- **Authentication**: None (can add custom headers)

### Azure DevOps
- **Inbound**: REST API calls
- **Authentication**: Personal Access Token
- **Endpoint**: `https://dev.azure.com/{org}/_apis/wit/workitems`

### Application Insights
- **Inbound**: Telemetry data
- **Protocol**: HTTPS
- **SDK**: Python Application Insights SDK

## Troubleshooting Flow

```
Issue Reported
    ↓
Check Application Insights Logs
    ↓
    ├─ HTTP 400? → Check Wiz payload format
    ├─ HTTP 401? → Verify PAT token and permissions
    ├─ HTTP 404? → Check Azure DevOps project name
    ├─ HTTP 500? → Review function logs for exceptions
    └─ Timeout? → Check Azure DevOps API availability
```

## Future Enhancements

### Potential Improvements
1. **Batch Processing**: Handle multiple findings in one request
2. **Duplicate Detection**: Check for existing work items
3. **Custom Fields**: Map more Wiz data to Azure DevOps fields
4. **Assignee Mapping**: Auto-assign based on resource owner
5. **State Transitions**: Update work items when issues resolve
6. **Enrichment**: Add related resources, attack paths
7. **Notifications**: Send alerts for critical findings
8. **Dashboard**: Create Power BI dashboard from logs

### Alternative Architectures
- **Event Grid**: Use Azure Event Grid for async processing
- **Logic Apps**: No-code alternative for simpler scenarios
- **Durable Functions**: For long-running workflows
- **API Management**: Add rate limiting, caching, transformation
