import azure.functions as func
import logging
import json
import os
from azure.identity import DefaultAzureCredential
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication


app = func.FunctionApp()


def format_description(issue_data):
    """
    Format a rich HTML description for the Azure DevOps work item from Wiz finding data.
    
    Args:
        issue_data: Dictionary containing the Wiz issue data
        
    Returns:
        Formatted HTML string
    """
    issue = issue_data.get('issue', {})
    resource = issue_data.get('resource', {})
    policy = issue_data.get('policy', {})
    trigger = issue_data.get('trigger', {})
    
    # Build structured description
    description_parts = [
        '<div style="font-family: Segoe UI, Arial, sans-serif;">',
        '<h2>🔍 Wiz Vulnerability Finding</h2>',
        '<hr/>',
    ]
    
    # Issue Summary Section
    description_parts.extend([
        '<h3>📋 Issue Summary</h3>',
        '<table style="border-collapse: collapse; width: 100%;">',
        f'<tr><td style="padding: 8px; font-weight: bold; width: 150px;">Issue Name:</td><td style="padding: 8px;">{issue.get("name", "N/A")}</td></tr>',
        f'<tr><td style="padding: 8px; font-weight: bold;">Status:</td><td style="padding: 8px;"><strong>{issue.get("status", "N/A")}</strong></td></tr>',
        f'<tr><td style="padding: 8px; font-weight: bold;">Severity:</td><td style="padding: 8px;"><span style="color: red;"><strong>{issue.get("severity", "N/A")}</strong></span></td></tr>',
        f'<tr><td style="padding: 8px; font-weight: bold;">Created:</td><td style="padding: 8px;">{issue.get("created", "N/A")}</td></tr>',
        f'<tr><td style="padding: 8px; font-weight: bold;">Issue ID:</td><td style="padding: 8px;"><code>{issue.get("id", "N/A")}</code></td></tr>',
        '</table>',
        '<br/>',
    ])
    
    # Description Section
    issue_description = issue.get('description', 'No description available')
    description_parts.extend([
        '<h3>📝 Description</h3>',
        f'<div style="background-color: #f5f5f5; padding: 12px; border-left: 4px solid #0078d4; margin: 10px 0;">{issue_description}</div>',
        '<br/>',
    ])
    
    # Resource Section
    cloud_platform = resource.get('cloudPlatform', 'N/A')
    description_parts.extend([
        '<h3>📦 Resource Details</h3>',
        '<table style="border-collapse: collapse; width: 100%;">',
        f'<tr><td style="padding: 8px; font-weight: bold; width: 150px;">Resource:</td><td style="padding: 8px;"><code>{resource.get("name", "N/A")}</code></td></tr>',
        f'<tr><td style="padding: 8px; font-weight: bold;">Resource Type:</td><td style="padding: 8px;">{resource.get("type", "N/A")}</td></tr>',
        f'<tr><td style="padding: 8px; font-weight: bold;">Cloud Platform:</td><td style="padding: 8px;">{cloud_platform}</td></tr>',
    ])
    
    # Add resource URL if available
    cloud_provider_url = resource.get('cloudProviderURL', '')
    if cloud_provider_url:
        description_parts.append(
            f'<tr><td style="padding: 8px; font-weight: bold;">Resource URL:</td><td style="padding: 8px;"><a href="{cloud_provider_url}" target="_blank">{cloud_provider_url}</a></td></tr>'
        )
    
    description_parts.extend([
        '</table>',
        '<br/>',
    ])
    
    # Wiz Reference Link
    ref_link = issue.get('refLink', '')
    if ref_link:
        description_parts.extend([
            '<h3>🔗 Wiz Issue Link</h3>',
            f'<p><a href="{ref_link}" target="_blank">View in Wiz Platform →</a></p>',
            '<br/>',
        ])
    
    # Policy Information
    policy_name = policy.get('name', '')
    if policy_name:
        description_parts.extend([
            '<h3>📜 Policy</h3>',
            '<table style="border-collapse: collapse; width: 100%;">',
            f'<tr><td style="padding: 8px; font-weight: bold; width: 150px;">Policy Name:</td><td style="padding: 8px;">{policy_name}</td></tr>',
            f'<tr><td style="padding: 8px; font-weight: bold;">Policy ID:</td><td style="padding: 8px;"><code>{policy.get("id", "N/A")}</code></td></tr>',
            '</table>',
            '<br/>',
        ])
    
    # Trigger Information
    trigger_type = trigger.get('type', '')
    if trigger_type:
        description_parts.extend([
            '<h3>⚡ Trigger Information</h3>',
            '<table style="border-collapse: collapse; width: 100%;">',
            f'<tr><td style="padding: 8px; font-weight: bold; width: 150px;">Trigger Type:</td><td style="padding: 8px;">{trigger_type}</td></tr>',
            f'<tr><td style="padding: 8px; font-weight: bold;">Rule Name:</td><td style="padding: 8px;">{trigger.get("ruleName", "N/A")}</td></tr>',
            '</table>',
            '<br/>',
        ])
    
    # Raw JSON (collapsible)
    description_parts.extend([
        '<details>',
        '<summary><strong>🔧 Raw JSON Payload (Click to expand)</strong></summary>',
        '<pre style="background-color: #f5f5f5; padding: 10px; overflow-x: auto; font-size: 12px;">',
        json.dumps(issue_data, indent=2),
        '</pre>',
        '</details>',
        '</div>',
    ])
    
    return ''.join(description_parts)


def create_work_item(issue_data):
    """
    Create a User Story work item in Azure DevOps from Wiz vulnerability finding.
    Uses Managed Identity for authentication.
    
    Args:
        issue_data: Dictionary containing the Wiz issue data
        
    Returns:
        Dictionary with work item details or error information
    """
    try:
        # Get Azure DevOps configuration from environment variables
        organization_url = os.environ.get('AZDO_ORG_URL')
        project_name = os.environ.get('AZDO_PROJECT')
        
        if not all([organization_url, project_name]):
            raise ValueError(
                "Missing required Azure DevOps configuration. "
                "Please set AZDO_ORG_URL and AZDO_PROJECT environment variables."
            )
        
        # Extract issue and resource information
        issue = issue_data.get('issue', {})
        resource = issue_data.get('resource', {})
        
        issue_name = issue.get('name', 'Unknown Issue')
        resource_name = resource.get('name', 'Unknown Resource')
        cloud_platform = resource.get('cloudPlatform', 'Unknown Platform')
        
        # Create work item title
        title = f"Wiz Vuln Findings - {issue_name}"
        
        # Format rich HTML description
        description = format_description(issue_data)
        
        # Use Managed Identity for authentication
        logging.info("Authenticating to Azure DevOps using Managed Identity")
        credential = DefaultAzureCredential()
        
        # Get access token for Azure DevOps
        token = credential.get_token("499b84ac-1321-427f-aa17-267ca6975798/.default")
        
        # Create connection to Azure DevOps using the token
        credentials = BasicAuthentication('', token.token)
        connection = Connection(base_url=organization_url, creds=credentials)
        
        # Get work item tracking client
        wit_client = connection.clients.get_work_item_tracking_client()
        
        # Build tags list
        tags_list = ["Wiz", "Vulnerability", "Security"]
        
        # Add cloud platform as tag
        if cloud_platform and cloud_platform != 'Unknown Platform':
            tags_list.append(f"Platform-{cloud_platform}")
        
        # Add severity as tag
        severity = issue.get('severity', '')
        if severity:
            tags_list.append(f"Severity-{severity}")
        
        # Add resource name as tag (shortened)
        if resource_name and resource_name != 'Unknown Resource':
            # Extract short name (last part after /)
            resource_short_name = resource_name.split('/')[-1] if '/' in resource_name else resource_name
            # Limit length and clean up
            resource_short_name = resource_short_name[:50].replace(' ', '-')
            tags_list.append(f"Resource-{resource_short_name}")
        
        tags_string = "; ".join(tags_list)
        
        # Define work item fields
        document = [
            {
                "op": "add",
                "path": "/fields/System.Title",
                "value": title
            },
            {
                "op": "add",
                "path": "/fields/System.Description",
                "value": description
            },
            {
                "op": "add",
                "path": "/fields/System.Tags",
                "value": tags_string
            }
        ]
        
        # Add priority based on severity
        if severity:
            priority_map = {
                'CRITICAL': 1,
                'HIGH': 2,
                'MEDIUM': 3,
                'LOW': 4,
                'INFORMATIONAL': 4
            }
            priority = priority_map.get(severity, 3)
            document.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.Priority",
                "value": priority
            })
        
        # Add acceptance criteria with remediation steps if available
        issue_description = issue.get('description', '')
        if issue_description:
            acceptance_criteria = f"""<div>
<h3>Remediation Steps:</h3>
<p>{issue_description}</p>
<br/>
<h3>Acceptance Criteria:</h3>
<ul>
<li>Vulnerability has been remediated as per the description above</li>
<li>Changes have been verified in the resource</li>
<li>Wiz scan confirms the issue is resolved</li>
</ul>
</div>"""
            
            document.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
                "value": acceptance_criteria
            })
        
        # Create the work item
        work_item = wit_client.create_work_item(
            document=document,
            project=project_name,
            type='Issue'
        )
        
        logging.info(f"Successfully created work item #{work_item.id}: {title}")
        logging.info(f"Resource: {resource_name}, Platform: {cloud_platform}, Severity: {severity}")
        
        return {
            "work_item_id": work_item.id,
            "work_item_url": work_item._links.additional_properties.get('html', {}).get('href'),
            "title": title,
            "resource": resource_name,
            "cloud_platform": cloud_platform,
            "severity": severity
        }
        
    except Exception as e:
        logging.error(f"Error creating Azure DevOps work item: {str(e)}")
        raise


@app.route(route="webhook", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def webhook(req: func.HttpRequest) -> func.HttpResponse:
    """
    Webhook endpoint that receives Wiz vulnerability findings and creates Azure DevOps work items.
    Accepts findings from any cloud platform.
    """
    logging.info('Wiz webhook triggered!')
    
    try:
        # Get the request body
        req_body = req.get_json()
        
        # Log the entire JSON body for debugging
        logging.info("=" * 50)
        logging.info("Received Wiz vulnerability payload:")
        logging.info(json.dumps(req_body, indent=2))
        logging.info("=" * 50)
        
        # Validate the payload structure
        if 'issue' not in req_body:
            return func.HttpResponse(
                json.dumps({
                    "status": "error",
                    "message": "Invalid payload structure. Expected 'issue' field in JSON."
                }),
                status_code=400,
                mimetype="application/json"
            )
        
        # Extract resource information for logging
        resource = req_body.get('resource', {})
        cloud_platform = resource.get('cloudPlatform', 'Unknown')
        resource_name = resource.get('name', 'Unknown')
        
        logging.info(f"Processing finding for resource: {resource_name}, platform: {cloud_platform}")
        
        # Create Azure DevOps work item
        work_item_result = create_work_item(req_body)
        
        # Return success response
        response_data = {
            "status": "success",
            "message": "Azure DevOps work item created successfully",
            "work_item": work_item_result,
            "received_issue": req_body.get('issue', {}).get('name'),
            "resource": resource_name,
            "cloud_platform": cloud_platform
        }
        
        logging.info(f"Response: {json.dumps(response_data, indent=2)}")
        
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json"
        )
        
    except ValueError as e:
        logging.error(f"JSON parsing error: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": "Invalid JSON payload",
                "error": str(e)
            }),
            status_code=400,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "message": "Failed to process webhook",
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
