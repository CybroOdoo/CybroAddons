## Module <onedrive_integration_odoo>
#### 11.12.2023
#### Version 16.0.1.0.0
#### ADD
- Initial commit for Onedrive Integration

#### 26.08.2024
#### Version 16.0.1.0.1
#### UPDT
-  Added modules field and changed view

#### 12.09.2025
#### Version 16.0.1.0.2
##### BUG FIX
- Updated the module workflow to remove the dependency on manually fetching the folder ID. Instead, a new Folder Name field was introduced in the Odoo settings, and the system now automatically retrieves the corresponding Folder ID from the Microsoft Graph API and stores it internally.
