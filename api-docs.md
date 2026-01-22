# FaceOn Entry System API

## Purpose
API for an advanced access control system utilizing two-factor authentication:
* **Possession**: QR Code generated per employee.
* **Inherence**: Biometric facial recognition using DeepFace.

## Access
Most endpoints under `/admin` require a valid JWT Bearer Token.


## Version: 1.0.0

### Available authorizations
#### OAuth2PasswordBearer (OAuth2, password)
Token URL: admin/login
Scopes:

---

### [GET] /admin/health
**Health Check**

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Successful Response | **application/json**: <br> |

### [GET] /admin/qr_test/{uuid_value}
**Qr Test**

Generates a QR code for the given UUID value.
On address /admin/qr_test/{uuid_value} you will get a QR code image.

#### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ------ |
| uuid_value | path |  | Yes | string |
| email | query |  | No | string |

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Successful Response | **application/json**: <br> |
| 422 | Validation Error | **application/json**: [HTTPValidationError](#httpvalidationerror)<br> |

### [POST] /admin/login
**Login For Access Token**

Administrator Login:
1. Checks if the user exists in the database.
2. Verifies the password (hash).
3. Returns a JWT token.

#### Request Body

| Required | Schema |
| -------- | ------ |
|  Yes | **application/x-www-form-urlencoded**: [Body_login_for_access_token_admin_login_post](#body_login_for_access_token_admin_login_post)<br> |

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Successful Response | **application/json**: [Token](#token)<br> |
| 422 | Validation Error | **application/json**: [HTTPValidationError](#httpvalidationerror)<br> |

### [POST] /admin/create_employee
**Create Employee**

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

#### Request Body

| Required | Schema |
| -------- | ------ |
|  Yes | **multipart/form-data**: [Body_create_employee_admin_create_employee_post](#body_create_employee_admin_create_employee_post)<br> |

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Successful Response | **application/json**: [EmployeeResponse](#employeeresponse)<br> |
| 422 | Validation Error | **application/json**: [HTTPValidationError](#httpvalidationerror)<br> |

##### Security

| Security Schema | Scopes |
| --------------- | ------ |
| OAuth2PasswordBearer |  |

### [GET] /admin/employees
**Get All Employees**

Retrieves a list of all registered employees.

Args:
    db (Session): Database session.
    current_admin (Admin): Authenticated administrator performing the request.

Returns:
    List[schemas.Employee]: A list of employee objects including their IDs,
                            names, emails, and account status.

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Successful Response | **application/json**: [ [EmployeeResponse](#employeeresponse) ]<br> |

##### Security

| Security Schema | Scopes |
| --------------- | ------ |
| OAuth2PasswordBearer |  |

### [PATCH] /admin/employees/{employee_uid}/status
**Update Employee Status**

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

#### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ------ |
| employee_uid | path |  | Yes | string |

#### Request Body

| Required | Schema |
| -------- | ------ |
|  No | **application/x-www-form-urlencoded**: [Body_update_employee_status_admin_employees__employee_uid__status_patch](#body_update_employee_status_admin_employees__employee_uid__status_patch)<br> |

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Successful Response | **application/json**: <br> |
| 422 | Validation Error | **application/json**: [HTTPValidationError](#httpvalidationerror)<br> |

##### Security

| Security Schema | Scopes |
| --------------- | ------ |
| OAuth2PasswordBearer |  |

### [PUT] /admin/employees/{employee_uid}
**Update Employee**

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

#### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ------ |
| employee_uid | path |  | Yes | string |

#### Request Body

| Required | Schema |
| -------- | ------ |
|  No | **multipart/form-data**: [Body_update_employee_admin_employees__employee_uid__put](#body_update_employee_admin_employees__employee_uid__put)<br> |

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Successful Response | **application/json**: <br> |
| 422 | Validation Error | **application/json**: [HTTPValidationError](#httpvalidationerror)<br> |

##### Security

| Security Schema | Scopes |
| --------------- | ------ |
| OAuth2PasswordBearer |  |

### [DELETE] /admin/employees/{employee_uid}
**Delete Employee**

Permanently removes an employee and their associated data from the system.

This action will also remove the employee's biometric embeddings and access logs.
Revokes access immediately as the QR code associated with this ID will no longer be valid.

Args:
    employee_id (int): The numeric ID of the employee to be deleted.
    db (Session): Database session.
    current_admin (Admin): Authenticated administrator performing the action.

Returns:
    dict: Success message upon deletion.

#### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ------ |
| employee_uid | path |  | Yes | string |

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Successful Response | **application/json**: <br> |
| 422 | Validation Error | **application/json**: [HTTPValidationError](#httpvalidationerror)<br> |

##### Security

| Security Schema | Scopes |
| --------------- | ------ |
| OAuth2PasswordBearer |  |

### [GET] /admin/logs
**Get Access Logs**

Retrieves all access logs recorded in the system.

Each log entry includes details such as timestamp, employee name,
access status, reason for denial (if applicable), and debug distance
for biometric checks.

Args:
    db (Session): Database session.
    current_admin (Admin): Authenticated administrator performing the request.

Returns:
    List[schemas.LogEntry]: A list of access log entries.

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Successful Response | **application/json**: [ [LogEntry](#logentry) ]<br> |

##### Security

| Security Schema | Scopes |
| --------------- | ------ |
| OAuth2PasswordBearer |  |

### [GET] /admin/logs/export
**Export Logs Csv**

Generates and returns a CSV file containing all access logs.

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Successful Response | **application/json**: <br> |

##### Security

| Security Schema | Scopes |
| --------------- | ------ |
| OAuth2PasswordBearer |  |

---

### [POST] /api/terminal/access-verify
**Verify Access**

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

#### Request Body

| Required | Schema |
| -------- | ------ |
|  Yes | **multipart/form-data**: [Body_verify_access_api_terminal_access_verify_post](#body_verify_access_api_terminal_access_verify_post)<br> |

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 200 | Successful Response | **application/json**: object<br> |
| 422 | Validation Error | **application/json**: [HTTPValidationError](#httpvalidationerror)<br> |

---
### Schemas

#### Body_create_employee_admin_create_employee_post

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| photo | binary |  | Yes |
| name | string |  | Yes |
| email | string |  | Yes |
| expiration_date |  |  | No |

#### Body_login_for_access_token_admin_login_post

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| grant_type |  |  | No |
| username | string |  | Yes |
| password | string |  | Yes |
| scope | string |  | No |
| client_id |  |  | No |
| client_secret |  |  | No |

#### Body_update_employee_admin_employees__employee_uid__put

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| name |  |  | No |
| email |  |  | No |
| photo | binary |  | No |
| is_active |  |  | No |
| expiration_date |  |  | No |

#### Body_update_employee_status_admin_employees__employee_uid__status_patch

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| is_active |  |  | No |
| expiration_date |  |  | No |

#### Body_verify_access_api_terminal_access_verify_post

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| employee_uid | string |  | Yes |
| file | binary |  | Yes |

#### EmployeeResponse

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| uuid | string (uuid) |  | Yes |
| name | string |  | Yes |
| email | string |  | Yes |
| is_active | boolean |  | Yes |
| expires_at |  |  | Yes |

#### HTTPValidationError

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| detail | [ [ValidationError](#validationerror) ] |  | No |

#### LogEntry

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| id | integer |  | Yes |
| timestamp | string |  | Yes |
| employee_name | string |  | Yes |
| status | string |  | Yes |
| reason |  |  | No |
| employee_email |  |  | No |
| debug_distance |  |  | No |

#### Token

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| access_token | string |  | Yes |
| token_type | string |  | Yes |

#### ValidationError

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| loc | [  ] |  | Yes |
| msg | string |  | Yes |
| type | string |  | Yes |
