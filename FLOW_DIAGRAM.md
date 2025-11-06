# GitHub Vulnerability Flow - Wiz to Azure DevOps

## Complete Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. Vulnerability Detection                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Wiz scans GitHub repository
                              ▼
                    ┌──────────────────┐
                    │   Wiz Platform   │
                    │                  │
                    │  Detects:        │
                    │  - TensorFlow    │
                    │    vulnerability │
                    │  - In repo:      │
                    │    org/repo/main │
                    └──────────────────┘
                              │
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      2. Webhook Triggered                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ POST /api/webhook
                              ▼
                    ┌──────────────────┐
                    │   Wiz sends:     │
                    ├──────────────────┤
                    │ {                │
                    │   "issue": {...},│
                    │   "resource": {  │
                    │     "cloudPlat...│
                    │     "GitHub"     │
                    │   }              │
                    │ }                │
                    └──────────────────┘
                              │
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    3. Azure Function Processing                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Azure Function   │
                    │ (Python 3.11)    │
                    └──────────────────┘
                              │
                              ├─────────────┐
                              │             │
                    ┌─────────▼──────┐  ┌──▼──────────────┐
                    │ Validate JSON  │  │ Check Platform  │
                    │ Has "issue"?   │  │ Is "GitHub"?    │
                    └────────┬───────┘  └──┬──────────────┘
                             │ YES         │ 
                             │             │
                             └─────┬───────┘
                                   │
                        ┌──────────▼───────────┐
                        │ Extract Information: │
                        ├──────────────────────┤
                        │ - Issue name         │
                        │ - Severity           │
                        │ - Description        │
                        │ - Repository         │
                        │ - GitHub URL         │
                        │ - Wiz link           │
                        └──────────┬───────────┘
                                   │
                        ┌──────────▼───────────┐
                        │ Format Rich HTML:    │
                        ├──────────────────────┤
                        │ - Summary table      │
                        │ - Description box    │
                        │ - Repo details       │
                        │ - Clickable links    │
                        │ - Policy info        │
                        │ - Raw JSON           │
                        └──────────┬───────────┘
                                   │
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                  4. Azure DevOps API Call                        │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │ Azure DevOps REST API    │
                    │ (with PAT auth)          │
                    └──────────────────────────┘
                                   │
                    ┌──────────────▼────────────────┐
                    │ Create Work Item:             │
                    ├───────────────────────────────┤
                    │ Type: User Story              │
                    │ Title: "Wiz Vuln - {name}"    │
                    │ Description: Rich HTML        │
                    │ Priority: Based on severity   │
                    │ Tags: Wiz, GitHub, Repo, etc. │
                    │ Acceptance Criteria: Remediate│
                    └──────────────┬────────────────┘
                                   │
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                  5. Work Item Created                            │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │  Azure DevOps            │
                    │  Work Item #12345        │
                    ├──────────────────────────┤
                    │  [x] Priority 2 (HIGH)   │
                    │  [x] Tags: Wiz, GitHub   │
                    │  [x] Rich description    │
                    │  [x] Links to GitHub     │
                    │  [x] Links to Wiz        │
                    └──────────────────────────┘
                                   │
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                     6. Developer Action                          │
└─────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │ Developer sees work item in  │
                    │ Azure DevOps Board           │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │ Clicks GitHub link to view   │
                    │ affected repository/file     │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │ Clicks Wiz link for full     │
                    │ security context             │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │ Follows remediation steps:   │
                    │ "Upgrade tensorflow to       │
                    │  version 2.14.1"             │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │ Creates PR with fix          │
                    │ Merges to main branch        │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │ Marks work item as Done      │
                    │ after Wiz confirms fix       │
                    └──────────────────────────────┘
```

---

## Detailed Flow Steps

### Step 1: Vulnerability Detection
**Actor**: Wiz Platform  
**Action**: Scans GitHub repository and detects vulnerability  
**Output**: Vulnerability finding record

**Example**:
- Repository: `timakondu/wiz-code-gha/main`
- Issue: Critical TensorFlow vulnerability
- Location: `/data/sensitive_data/requirements.txt`
- Severity: HIGH

---

### Step 2: Webhook Triggered
**Actor**: Wiz Platform  
**Action**: Sends HTTP POST to Azure Function webhook  
**Payload**:
```json
{
  "trigger": { "type": "Manual", "ruleName": "Manual" },
  "issue": {
    "id": "cb0ac949-...",
    "name": "Critical Vulnerability in TensorFlow",
    "severity": "HIGH",
    "description": "Upgrade tensorflow to 2.14.1",
    "refLink": "https://app.wiz.io/issues#..."
  },
  "resource": {
    "name": "timakondu/wiz-code-gha/main",
    "cloudPlatform": "GitHub",
    "cloudProviderURL": "https://github.com/..."
  }
}
```

---

### Step 3: Azure Function Processing
**Actor**: Azure Function (Python)  
**Actions**:

1. **Receive Request**
   - Parse JSON body
   - Log full payload

2. **Validate Structure**
   - Check for `issue` field
   - Return 400 if missing

3. **Validate Platform**
   - Check `resource.cloudPlatform === "GitHub"`
   - Skip with 200 if not GitHub
   - Log warning for non-GitHub

4. **Extract Data**
   ```python
   issue_name = issue.get('name')
   severity = issue.get('severity')
   repo_name = resource.get('name')
   github_url = resource.get('cloudProviderURL')
   wiz_link = issue.get('refLink')
   ```

5. **Format HTML Description**
   - Create summary table
   - Add description with highlighting
   - Add repository details
   - Add clickable links
   - Add policy and trigger info
   - Add collapsible raw JSON

6. **Calculate Priority**
   ```python
   priority_map = {
     'CRITICAL': 1,
     'HIGH': 2,
     'MEDIUM': 3,
     'LOW': 4
   }
   priority = priority_map.get(severity, 3)
   ```

7. **Build Tags**
   ```python
   tags = [
     "Wiz",
     "Vulnerability", 
     "Security",
     "GitHub",
     f"Severity-{severity}",
     f"Repo-{repo_short_name}"
   ]
   ```

---

### Step 4: Azure DevOps API Call
**Actor**: Azure Function  
**Action**: Call Azure DevOps REST API  
**Authentication**: Personal Access Token (PAT)

**Request**:
```python
POST https://dev.azure.com/{org}/{project}/_apis/wit/workitems/$User Story
Authorization: Basic {PAT}
Content-Type: application/json-patch+json

[
  {
    "op": "add",
    "path": "/fields/System.Title",
    "value": "Wiz Vuln Findings - Critical Vulnerability in TensorFlow"
  },
  {
    "op": "add",
    "path": "/fields/System.Description",
    "value": "<html>..."
  },
  {
    "op": "add",
    "path": "/fields/Microsoft.VSTS.Common.Priority",
    "value": 2
  },
  {
    "op": "add",
    "path": "/fields/System.Tags",
    "value": "Wiz; Vulnerability; Security; GitHub; Severity-HIGH; Repo-wiz-code-gha"
  }
]
```

**Response**:
```json
{
  "id": 12345,
  "url": "https://dev.azure.com/.../workitems/12345",
  "_links": {
    "html": {
      "href": "https://dev.azure.com/.../edit/12345"
    }
  }
}
```

---

### Step 5: Work Item Created
**Actor**: Azure DevOps  
**Result**: New User Story work item

**Work Item Details**:
- **ID**: #12345
- **Type**: User Story 🎯
- **State**: New
- **Priority**: 2 🟠
- **Title**: "Wiz Vuln Findings - Critical Vulnerability in TensorFlow"
- **Description**: Rich HTML with all details
- **Tags**: `Wiz | Vulnerability | Security | GitHub | Severity-HIGH | Repo-wiz-code-gha`
- **Acceptance Criteria**: Remediation steps + verification checklist

**Visible On**:
- Azure DevOps Boards
- Work Items list
- Backlogs
- Sprint boards
- Queries

---

### Step 6: Developer Action
**Actor**: Development Team  
**Workflow**:

1. **Discovery**
   - See work item in daily standup
   - Board shows as high priority (Priority 2)
   - Tags indicate it's a GitHub/Wiz finding

2. **Investigation**
   - Open work item in Azure DevOps
   - Read formatted description
   - Click GitHub URL → View affected file
   - Click Wiz URL → See full security context

3. **Remediation**
   - Read acceptance criteria
   - Follow remediation steps: "Upgrade tensorflow to 2.14.1"
   - Update `requirements.txt`
   - Test changes locally

4. **Submission**
   - Create pull request
   - Get code review
   - Merge to main branch

5. **Verification**
   - Wiz rescans repository
   - Confirms vulnerability is resolved
   - Mark work item as Done

---

## Alternative Flows

### Flow A: Non-GitHub Resource (Skipped)

```
Wiz Detects AWS EC2 Vulnerability
    ↓
Sends webhook with cloudPlatform: "AWS"
    ↓
Azure Function validates
    ↓
    ├─ Platform ≠ GitHub
    ↓
Log warning + Return 200 with "skipped" status
    ↓
No work item created
```

**Response**:
```json
{
  "status": "skipped",
  "message": "This webhook is configured for GitHub resources only. Received: AWS",
  "cloud_platform": "AWS"
}
```

---

### Flow B: Invalid Payload (Error)

```
Wiz (or other) sends invalid payload
    ↓
Missing "issue" field in JSON
    ↓
Azure Function validates
    ↓
    ├─ Validation fails
    ↓
Return 400 Bad Request
```

**Response**:
```json
{
  "status": "error",
  "message": "Invalid payload structure. Expected 'issue' field in JSON."
}
```

---

### Flow C: Azure DevOps API Error

```
Valid GitHub webhook received
    ↓
Function processes successfully
    ↓
Calls Azure DevOps API
    ↓
    ├─ PAT expired / Invalid permissions
    ↓
Exception caught
    ↓
Return 500 Internal Server Error
```

**Response**:
```json
{
  "status": "error",
  "message": "Failed to process webhook",
  "error": "401 Unauthorized: Check PAT token"
}
```

---

## Data Flow Diagram

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│   Wiz    │──JSON──▶│ Function │──API───▶│  Azure   │
│ Platform │◀─200────│  (HTTP)  │◀─Work───│  DevOps  │
└──────────┘         └──────────┘   Item  └──────────┘
                           │
                           │ Logs
                           ▼
                    ┌──────────┐
                    │   App    │
                    │ Insights │
                    └──────────┘
```

---

## Timing Expectations

| Step | Expected Duration | Notes |
|------|------------------|-------|
| Wiz Detection | Varies | Depends on scan schedule |
| Webhook Send | < 1 second | Near real-time |
| Function Cold Start | 1-3 seconds | First call only |
| Function Warm | < 500ms | Subsequent calls |
| Azure DevOps API | 1-2 seconds | Work item creation |
| Total End-to-End | 2-5 seconds | From webhook to work item |
| Developer Notification | Varies | Depends on Azure DevOps rules |

---

## Error Handling at Each Step

### Step 1: Wiz Detection
- **Error**: Scan fails
- **Impact**: No webhook sent
- **Resolution**: Wiz platform handles

### Step 2: Webhook Send
- **Error**: Network failure, function unavailable
- **Impact**: Webhook fails, may retry
- **Resolution**: Wiz retry logic, check function availability

### Step 3: Function Processing
- **Error**: Invalid JSON, missing fields, non-GitHub platform
- **Impact**: Return error or skip
- **Resolution**: Fix webhook configuration in Wiz

### Step 4: Azure DevOps API
- **Error**: PAT expired, invalid project, permissions
- **Impact**: Work item not created, 500 error
- **Resolution**: Update PAT, check permissions

### Step 5: Work Item Creation
- **Error**: Required fields missing, invalid field values
- **Impact**: API returns error
- **Resolution**: Check field mappings in function

### Step 6: Developer Action
- **Error**: Developer doesn't see work item
- **Impact**: Vulnerability not remediated
- **Resolution**: Check Azure DevOps notifications, queries

---

## Monitoring Points

### 1. Function Metrics
- Execution count
- Success rate
- Response time
- Error rate

### 2. Azure DevOps Metrics
- Work items created per day
- Average time to resolution
- Open vs. closed ratio
- Distribution by severity

### 3. Integration Health
- Webhook success rate
- Platform validation (GitHub vs. others)
- API call success rate
- End-to-end latency

---

## Success Criteria

✅ Webhook receives GitHub finding  
✅ Function validates and processes  
✅ Work item created in < 5 seconds  
✅ Description properly formatted  
✅ All links are clickable  
✅ Tags correctly applied  
✅ Developer can easily remediate  
✅ Work item tracks to completion  
