# Managed Identity Setup Guide

## Overview

This integration uses **Azure Managed Identity** for authentication instead of Personal Access Tokens (PAT). This is more secure and eliminates the need to manage and rotate credentials.

## What is Managed Identity?

Managed Identity is an Azure AD identity that is automatically managed by Azure. Your Function App has been configured with a **System-Assigned Managed Identity**, which means it has its own identity in Azure AD that can be granted permissions to other services.

## Setup Steps

### Step 1: Deploy the Infrastructure

First, deploy your Terraform infrastructure:

```bash
terraform init
terraform apply
```

After deployment, note the outputs:
```bash
terraform output
```

You'll see:
- `managed_identity_principal_id` - The unique ID of the managed identity
- `managed_identity_service_principal_name` - The display name (function app name)
- `webhook_url` - Your webhook endpoint

### Step 2: Add Managed Identity to Azure DevOps

You need to grant the Function App's managed identity access to create work items in Azure DevOps.

#### Option A: Using Azure DevOps Web UI (Recommended)

1. **Navigate to your Azure DevOps Organization**
   - Go to: `https://dev.azure.com/YOUR_ORG`

2. **Open Organization Settings**
   - Click the gear icon (⚙️) in the bottom left
   - Select "Organization settings"

3. **Add the Service Principal as a User**
   - In the left menu, click "Users"
   - Click "+ Add users" button
   - In the "Users or Service Principals" field, paste the **Principal ID** from Terraform output:
     ```
     <managed_identity_principal_id from terraform output>
     ```
   - Set Access Level: **Basic** (or higher)
   - Click "Add"

4. **Grant Project Permissions**
   - Navigate to your project: `https://dev.azure.com/YOUR_ORG/YOUR_PROJECT`
   - Click "Project settings" (gear icon in bottom left)
   - Select "Permissions" under "General"
   - Click "Add" → "Add Azure AD user or group"
   - Search for the service principal name (the function app name)
   - Add it with appropriate permissions

5. **Grant Work Item Permissions**
   - In Project Settings → Permissions
   - Find the managed identity user
   - Ensure it has these permissions:
     - ✅ View work items in this node
     - ✅ Edit work items in this node
     - ✅ Create work items in this node (under Area Path)

#### Option B: Using Azure CLI

```bash
# Get the managed identity details
PRINCIPAL_ID=$(terraform output -raw managed_identity_principal_id)
ORG_URL=$(terraform output -raw azdo_org_url | sed 's|https://dev.azure.com/||')

# Note: You'll need to use the Azure DevOps API or az devops CLI
# The service principal must be added via the web UI or API
```

#### Option C: Using Azure DevOps REST API

```bash
# Get the principal ID
PRINCIPAL_ID=$(terraform output -raw managed_identity_principal_id)

# Add user to organization (requires admin PAT for this step)
curl -X POST \
  "https://vsaex.dev.azure.com/YOUR_ORG/_apis/userentitlements?api-version=7.1-preview.3" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n :YOUR_ADMIN_PAT | base64)" \
  -d "{
    \"accessLevel\": {
      \"accountLicenseType\": \"express\"
    },
    \"user\": {
      \"principalName\": \"$PRINCIPAL_ID\",
      \"subjectKind\": \"servicePrincipal\"
    },
    \"projectEntitlements\": [{
      \"group\": {
        \"groupType\": \"projectContributor\"
      },
      \"projectRef\": {
        \"id\": \"YOUR_PROJECT_ID\"
      }
    }]
  }"
```

### Step 3: Verify Access

Test that the managed identity has access:

1. **Deploy the Function Code**
   ```bash
   func azure functionapp publish $(terraform output -raw function_app_name)
   ```

2. **Test the Webhook**
   ```bash
   curl -X POST $(terraform output -raw webhook_url) \
     -H "Content-Type: application/json" \
     -d @sample_payload.json
   ```

3. **Check the Response**
   - Should return HTTP 200 with work item details
   - If you get 401 Unauthorized, the managed identity doesn't have access yet

4. **View Function Logs**
   ```bash
   az functionapp log tail \
     --name $(terraform output -raw function_app_name) \
     --resource-group rg-webhook-function
   ```

### Step 4: Verify Work Item Created

1. Go to Azure DevOps: `https://dev.azure.com/YOUR_ORG/YOUR_PROJECT`
2. Navigate to Boards → Work Items
3. Look for a new User Story with "Wiz Vuln Findings" in the title

## Troubleshooting

### Error: "401 Unauthorized" when creating work item

**Cause**: The managed identity doesn't have permissions in Azure DevOps yet.

**Solution**:
1. Verify the managed identity was added to Azure DevOps organization
2. Check that it's added to the specific project
3. Verify it has work item permissions (View, Edit, Create)
4. Wait a few minutes for permissions to propagate

### Error: "Service principal not found"

**Cause**: Azure DevOps can't find the managed identity by Principal ID.

**Solution**:
1. Double-check you're using the Principal ID (not Tenant ID)
2. Make sure you're in the correct Azure AD tenant
3. Try using the Azure portal to manually add the managed identity:
   - Go to Azure DevOps → Organization Settings → Users
   - Click "+ Add users"
   - Search for the function app name or Principal ID

### Error: "Insufficient permissions to create work item"

**Cause**: The managed identity has access to Azure DevOps but not the right permissions.

**Solution**:
1. In Azure DevOps Project Settings → Permissions
2. Find the managed identity
3. Ensure these are set to "Allow":
   - View work items in this node
   - Edit work items in this node
   - Create work items in this node

### Can't find the service principal in Azure DevOps

**Workaround**: The Principal ID format might need adjustment. Try:

1. Get the enterprise application:
   ```bash
   az ad sp show --id $(terraform output -raw managed_identity_principal_id)
   ```

2. Use the `appId` or `displayName` from the output instead

## Security Benefits

### Why Managed Identity is Better than PAT

✅ **No Credential Management**: No passwords or tokens to store  
✅ **Automatic Rotation**: Azure handles credential lifecycle  
✅ **No Expiration**: Won't suddenly stop working after 90 days  
✅ **Audit Trail**: Azure AD logs all access  
✅ **Least Privilege**: Can grant specific permissions  
✅ **No Secret Leakage**: No tokens in environment variables or code  

### Security Best Practices

1. **Principle of Least Privilege**
   - Only grant the minimum required permissions
   - Limit to specific projects if possible

2. **Regular Access Review**
   - Periodically review what the managed identity has access to
   - Remove access to projects it no longer needs

3. **Monitor Access**
   - Check Azure AD sign-in logs for the managed identity
   - Set up alerts for unusual activity

4. **Conditional Access**
   - Consider applying conditional access policies
   - Restrict access to specific IP ranges if needed

## Verification Checklist

- [ ] Terraform deployed successfully
- [ ] Managed identity Principal ID obtained
- [ ] Service principal added to Azure DevOps organization
- [ ] Service principal added to project
- [ ] Work item permissions granted
- [ ] Function code deployed
- [ ] Test webhook returns 200 OK
- [ ] Work item created in Azure DevOps
- [ ] Function logs show successful authentication

## Advanced Configuration

### Granting Access to Multiple Projects

If you need the function to create work items in multiple projects:

1. Add the managed identity to each project
2. Update the `AZDO_PROJECT` environment variable as needed
3. Or modify the function code to accept project name in the payload

### Using User-Assigned Managed Identity

If you prefer a user-assigned managed identity:

1. Create the identity in Terraform:
   ```hcl
   resource "azurerm_user_assigned_identity" "function_identity" {
     name                = "id-wiz-function"
     resource_group_name = azurerm_resource_group.rg.name
     location            = azurerm_resource_group.rg.location
   }
   ```

2. Update the Function App:
   ```hcl
   identity {
     type = "UserAssigned"
     identity_ids = [azurerm_user_assigned_identity.function_identity.id]
   }
   ```

3. Update the Python code to use the client ID:
   ```python
   credential = ManagedIdentityCredential(client_id="<client-id>")
   ```

## Additional Resources

- [Managed Identities for Azure Resources](https://docs.microsoft.com/azure/active-directory/managed-identities-azure-resources/)
- [Azure DevOps Service Principals](https://docs.microsoft.com/azure/devops/organizations/accounts/add-organization-users)
- [Azure Functions Managed Identity](https://docs.microsoft.com/azure/app-service/overview-managed-identity)
- [Azure DevOps REST API](https://docs.microsoft.com/rest/api/azure/devops/)

## Getting Help

If you're still having issues:

1. Check the Function App logs in Application Insights
2. Verify the managed identity exists in Azure AD
3. Confirm the identity is added to Azure DevOps
4. Test with a simple API call to verify permissions
5. Review the Azure AD sign-in logs for authentication attempts
