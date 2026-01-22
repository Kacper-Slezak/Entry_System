# FaceOn Entry System API

> Version 1.0.0


    ## Purpose
    API for an advanced access control system utilizing two-factor authentication:
    * **Possession**: QR Code generated per employee.
    * **Inherence**: Biometric facial recognition using DeepFace.

    ## Access
    Most endpoints under `/admin` require a valid JWT Bearer Token.


## Path Table

| Method | Path | Description |
| --- | --- | --- |
| GET | [/admin/health](#getadminhealth) | Health Check |
| GET | [/admin/qr_test/{uuid_value}](#getadminqr_testuuid_value) | Qr Test |
| POST | [/admin/login](#postadminlogin) | Login For Access Token |
| POST | [/admin/create_employee](#postadmincreate_employee) | Create Employee |
| GET | [/admin/employees](#getadminemployees) | Get All Employees |
| PATCH | [/admin/employees/{employee_uid}/status](#patchadminemployeesemployee_uidstatus) | Update Employee Status |
| PUT | [/admin/employees/{employee_uid}](#putadminemployeesemployee_uid) | Update Employee |
| DELETE | [/admin/employees/{employee_uid}](#deleteadminemployeesemployee_uid) | Delete Employee |
| GET | [/admin/logs](#getadminlogs) | Get Access Logs |
| GET | [/admin/logs/export](#getadminlogsexport) | Export Logs Csv |
| POST | [/api/terminal/access-verify](#postapiterminalaccess-verify) | Verify Access |

## Reference Table

| Name | Path | Description |
| --- | --- | --- |
| Body_create_employee_admin_create_employee_post | [#/components/schemas/Body_create_employee_admin_create_employee_post](#componentsschemasbody_create_employee_admin_create_employee_post) |  |
| Body_login_for_access_token_admin_login_post | [#/components/schemas/Body_login_for_access_token_admin_login_post](#componentsschemasbody_login_for_access_token_admin_login_post) |  |
| Body_update_employee_admin_employees__employee_uid__put | [#/components/schemas/Body_update_employee_admin_employees__employee_uid__put](#componentsschemasbody_update_employee_admin_employees__employee_uid__put) |  |
| Body_update_employee_status_admin_employees__employee_uid__status_patch | [#/components/schemas/Body_update_employee_status_admin_employees__employee_uid__status_patch](#componentsschemasbody_update_employee_status_admin_employees__employee_uid__status_patch) |  |
| Body_verify_access_api_terminal_access_verify_post | [#/components/schemas/Body_verify_access_api_terminal_access_verify_post](#componentsschemasbody_verify_access_api_terminal_access_verify_post) |  |
| EmployeeResponse | [#/components/schemas/EmployeeResponse](#componentsschemasemployeeresponse) |  |
| HTTPValidationError | [#/components/schemas/HTTPValidationError](#componentsschemashttpvalidationerror) |  |
| LogEntry | [#/components/schemas/LogEntry](#componentsschemaslogentry) |  |
| Token | [#/components/schemas/Token](#componentsschemastoken) |  |
| ValidationError | [#/components/schemas/ValidationError](#componentsschemasvalidationerror) |  |
| OAuth2PasswordBearer | [#/components/securitySchemes/OAuth2PasswordBearer](#componentssecurityschemesoauth2passwordbearer) |  |

## Path Details

***

### [GET] /admin/health

- Summary
Health Check

- Operation id
health_check_admin_health_get

#### Responses

- 200 Successful Response

`application/json`

```typescript
{}
```

***

### [GET] /admin/qr_test/{uuid_value}

- Summary
Qr Test

- Operation id
qr_test_admin_qr_test__uuid_value__get

- Description
Generates a QR code for the given UUID value.
On address /admin/qr_test/{uuid_value} you will get a QR code image.

#### Parameters(Query)

```typescript
email?: string
```

#### Responses

- 200 Successful Response

`application/json`

```typescript
{}
```

- 422 Validation Error

`application/json`

```typescript
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [POST] /admin/login

- Summary
Login For Access Token

- Operation id
login_for_access_token_admin_login_post

- Description
Administrator Login:
1. Checks if the user exists in the database.
2. Verifies the password (hash).
3. Returns a JWT token.

#### RequestBody

- application/x-www-form-urlencoded

```typescript
{
  grant_type?: Partial(string) & Partial(null)
  username: string
  password: string
  scope?: string
  client_id?: Partial(string) & Partial(null)
  client_secret?: Partial(string) & Partial(null)
}
```

#### Responses

- 200 Successful Response

`application/json`

```typescript
{
  access_token: string
  token_type: string
}
```

- 422 Validation Error

`application/json`

```typescript
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [POST] /admin/create_employee

- Summary
Create Employee

- Operation id
create_employee_admin_create_employee_post

- Description
Registers a new employee and triggers credentials delivery.

Workflow:
1. Processes the photo to generate a 512-D biometric embedding.
2. Sets an account expiration date (defaults to 182 days if not provided).
3. Generates a unique QR code and sends it via email as a background task.

Args:
    photo (UploadFile): Initial biometric reference photo.
    name (str): Full name of the employee.
    email (str): Contact email for QR code delivery.
    expiration_date (datetime, optional): Specific timestamp for account expiration.
    db (Session): Database session.
    current_admin (Admin): Authenticated administrator.

Returns:
    EmployeeResponse: The newly created employee record.

Security
- OAuth2PasswordBearer

#### RequestBody

- multipart/form-data

```typescript
{
  photo: string
  name: string
  email: string
  expiration_date?: Partial(string) & Partial(null)
}
```

#### Responses

- 200 Successful Response

`application/json`

```typescript
{
  uuid: string
  name: string
  email: string
  is_active: boolean
  expires_at: Partial(string) & Partial(null)
}
```

- 422 Validation Error

`application/json`

```typescript
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [GET] /admin/employees

- Summary
Get All Employees

- Operation id
get_all_employees_admin_employees_get

- Description
Retrieves a list of all registered employees.

Args:
    db (Session): Database session.
    current_admin (Admin): Authenticated administrator performing the request.

Returns:
    List[schemas.Employee]: A list of employee objects including their IDs,
                            names, emails, and account status.

Security
- OAuth2PasswordBearer

#### Responses

- 200 Successful Response

`application/json`

```typescript
{
  uuid: string
  name: string
  email: string
  is_active: boolean
  expires_at: Partial(string) & Partial(null)
}[]
```

***

### [PATCH] /admin/employees/{employee_uid}/status

- Summary
Update Employee Status

- Operation id
update_employee_status_admin_employees__employee_uid__status_patch

- Description
Updates the access status and specific expiration timestamp for an employee.

This endpoint is intended for quick administrative actions, such as
instantly revoking access or setting a specific date/time when the
employee's QR/access should expire.

Args:
    employee_uid (str): The unique UUID of the employee.
    is_active (bool, optional): The new active status. If not provided,
        the current status remains unchanged.
    expiration_date (datetime, optional): A specific timestamp (ISO 8601)
        representing when the employee's access expires.
    db (Session): Database session dependency.
    current_admin (Admin): The authenticated administrator performing the action.

Returns:
    dict: A success message along with the updated status and expiration date.

Raises:
    HTTPException:
        - 400: If the UUID format is invalid.
        - 404: If no employee is found with the provided UUID.

Security
- OAuth2PasswordBearer

#### RequestBody

- application/x-www-form-urlencoded

```typescript
{
  "allOf": [
    {
      "$ref": "#/components/schemas/Body_update_employee_status_admin_employees__employee_uid__status_patch"
    }
  ],
  "title": "Body"
}
```

#### Responses

- 200 Successful Response

`application/json`

```typescript
{}
```

- 422 Validation Error

`application/json`

```typescript
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [PUT] /admin/employees/{employee_uid}

- Summary
Update Employee

- Operation id
update_employee_admin_employees__employee_uid__put

- Description
Updates an existing employee's full profile information.

This endpoint allows for a comprehensive update, including personal details,
biometrics (via photo upload), and administrative access controls. If a new
photo is uploaded, the system re-calculates the facial embedding vector.

Args:
    employee_uid (str): Unique identifier of the employee to be updated.
    name (str, optional): New full name of the employee.
    email (str, optional): New email address (must be unique across the system).
    photo (UploadFile, optional): New reference image for facial recognition.
    is_active (bool, optional): Administrative override to enable/disable access.
    expiration_date (datetime, optional): Specific timestamp for access expiration.
    db (Session): Database session dependency.
    current_admin (Admin): The authenticated administrator performing the update.

Returns:
    dict: Confirmation message and the updated employee UUID.

Raises:
    HTTPException:
        - 400: Invalid UUID, email already taken, or no face detected in photo.
        - 404: Employee not found.

Security
- OAuth2PasswordBearer

#### RequestBody

- multipart/form-data

```typescript
{
  "allOf": [
    {
      "$ref": "#/components/schemas/Body_update_employee_admin_employees__employee_uid__put"
    }
  ],
  "title": "Body"
}
```

#### Responses

- 200 Successful Response

`application/json`

```typescript
{}
```

- 422 Validation Error

`application/json`

```typescript
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [DELETE] /admin/employees/{employee_uid}

- Summary
Delete Employee

- Operation id
delete_employee_admin_employees__employee_uid__delete

- Description
Permanently removes an employee and their associated data from the system.

This action will also remove the employee's biometric embeddings and access logs.
Revokes access immediately as the QR code associated with this ID will no longer be valid.

Args:
    employee_id (int): The numeric ID of the employee to be deleted.
    db (Session): Database session.
    current_admin (Admin): Authenticated administrator performing the action.

Returns:
    dict: Success message upon deletion.

Security
- OAuth2PasswordBearer

#### Responses

- 200 Successful Response

`application/json`

```typescript
{}
```

- 422 Validation Error

`application/json`

```typescript
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

***

### [GET] /admin/logs

- Summary
Get Access Logs

- Operation id
get_access_logs_admin_logs_get

- Description
Retrieves all access logs recorded in the system.

Each log entry includes details such as timestamp, employee name,
access status, reason for denial (if applicable).

Args:
    db (Session): Database session.
    current_admin (Admin): Authenticated administrator performing the request.

Returns:
    List[schemas.LogEntry]: A list of access log entries.

Security
- OAuth2PasswordBearer

#### Responses

- 200 Successful Response

`application/json`

```typescript
{
  id: integer
  timestamp: string
  employee_name: string
  status: string
  reason?: Partial(string) & Partial(null)
  employee_email?: Partial(string) & Partial(null)
}[]
```

***

### [GET] /admin/logs/export

- Summary
Export Logs Csv

- Operation id
export_logs_csv_admin_logs_export_get

- Description
Generates and returns a CSV file containing all access logs.

Security
- OAuth2PasswordBearer

#### Responses

- 200 Successful Response

`application/json`

```typescript
{}
```

***

### [POST] /api/terminal/access-verify

- Summary
Verify Access

- Operation id
verify_access_api_terminal_access_verify_post

- Description
Verifies employee identity using a 2FA flow (QR Code + Face Recognition).

This endpoint validates the scanned QR UUID, checks the employee's status/expiry,
and performs a biometric comparison between the live photo and the stored template.

Args:
    employee_uid (str): The unique identifier decoded from the employee's QR code.
    file (UploadFile): Real-time image capture from the terminal camera.
    db (Session): Database session provided by the dependency injection.

Returns:
    Dict[str, Any]: A dictionary containing:
        - access (str): "GRANTED" if both factors pass, "DENIED" otherwise.
        - reason (str, optional): The cause of denial (e.g., "FACE_MISMATCH").
        - name (str, optional): Employee's full name if access is granted.

Note:
    The biometric threshold is currently set to 0.3 for the Facenet512 model.

#### RequestBody

- multipart/form-data

```typescript
{
  employee_uid: string
  file: string
}
```

#### Responses

- 200 Successful Response

`application/json`

```typescript
{
}
```

- 422 Validation Error

`application/json`

```typescript
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

## References

### #/components/schemas/Body_create_employee_admin_create_employee_post

```typescript
{
  photo: string
  name: string
  email: string
  expiration_date?: Partial(string) & Partial(null)
}
```

### #/components/schemas/Body_login_for_access_token_admin_login_post

```typescript
{
  grant_type?: Partial(string) & Partial(null)
  username: string
  password: string
  scope?: string
  client_id?: Partial(string) & Partial(null)
  client_secret?: Partial(string) & Partial(null)
}
```

### #/components/schemas/Body_update_employee_admin_employees__employee_uid__put

```typescript
{
  name?: Partial(string) & Partial(null)
  email?: Partial(string) & Partial(null)
  photo?: string
  is_active?: Partial(boolean) & Partial(null)
  expiration_date?: Partial(string) & Partial(null)
}
```

### #/components/schemas/Body_update_employee_status_admin_employees__employee_uid__status_patch

```typescript
{
  is_active?: Partial(boolean) & Partial(null)
  expiration_date?: Partial(string) & Partial(null)
}
```

### #/components/schemas/Body_verify_access_api_terminal_access_verify_post

```typescript
{
  employee_uid: string
  file: string
}
```

### #/components/schemas/EmployeeResponse

```typescript
{
  uuid: string
  name: string
  email: string
  is_active: boolean
  expires_at: Partial(string) & Partial(null)
}
```

### #/components/schemas/HTTPValidationError

```typescript
{
  detail: {
    loc?: Partial(string) & Partial(integer)[]
    msg: string
    type: string
  }[]
}
```

### #/components/schemas/LogEntry

```typescript
{
  id: integer
  timestamp: string
  employee_name: string
  status: string
  reason?: Partial(string) & Partial(null)
  employee_email?: Partial(string) & Partial(null)
  debug_distance?: Partial(number) & Partial(null)
}
```

### #/components/schemas/Token

```typescript
{
  access_token: string
  token_type: string
}
```

### #/components/schemas/ValidationError

```typescript
{
  loc?: Partial(string) & Partial(integer)[]
  msg: string
  type: string
}
```

### #/components/securitySchemes/OAuth2PasswordBearer

```typescript
{
  "type": "oauth2",
  "flows": {
    "password": {
      "scopes": {},
      "tokenUrl": "admin/login"
    }
  }
}
```
