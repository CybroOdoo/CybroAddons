## Module <auto_database_backup>

#### 30.09.2024
#### Version 18.0.1.0.0
#### ADD

- Initial commit for Automatic Database Backup To Local Server, Remote Server,
  Google Drive, Dropbox, Onedrive, Nextcloud and Amazon S3 Odoo18.

#### 29.10.2024
#### Version 18.0.2.0.0
#### UPDT

- Added feature to set Multi-Level Backup Storage, Store backups in multiple
  locations based on different intervals.

#### 13.05.2025
#### Version 18.0.2.0.1
#### UPDT

- Updated the function that uploads the database backup to OneDrive by adding a
  header configurator and fixed the issue where enabling 'Remove Old Backups'
  would delete all backups without uploading a new one.

#### 10.08.2026
#### Version 18.0.2.0.2
#### UPDT

- Added support for Azure Blob Storage, Google Cloud Storage, WebDAV, and custom
  S3-compatible endpoints.
- Added Multi-Database backup scope (Single, All, or Selected databases), Backup
  History tracking and execution logging, "Backup Now" and "Download Backup"
  header actions.
- Added Support Ticket submission wizard and top-bar Systray launcher.