.. image:: https://img.shields.io/badge/licence-LGPL--3-green.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

Automatic Database Backup To Local Server, Remote Server, Google Drive, Dropbox, Onedrive, Nextcloud and Amazon S3
==================================================================================================================
* Generate Database Backups and store to multiple locations


Overview
========
Automatic Database Backup lets you schedule and generate database (and
filestore) backups automatically and store them across a wide range of local
and cloud destinations. Configure a backup once, pick a destination, test the
connection, and let the scheduled actions run daily, weekly or monthly. You can
also trigger a backup on demand or download a fresh backup straight from the
configuration form.

Supported Backup Destinations
=============================
* **Local Server** - Store backups in any folder on the Odoo server.
* **FTP** - Push backups to a remote FTP server.
* **SFTP** - Push backups to a remote server over secure SFTP (Paramiko).
* **Google Drive** - Upload backups to a Google Drive account and folder.
* **Dropbox** - Upload backups to a connected Dropbox account.
* **Microsoft OneDrive** - Upload backups to OneDrive via OAuth.
* **Nextcloud** - Store backups on a self-hosted Nextcloud server.
* **Amazon S3** - Store backups in an Amazon S3 bucket.
* **S3-Compatible providers** - Use any S3-compatible storage through a custom
  endpoint URL and region: Backblaze B2, Wasabi, Cloudflare R2, MinIO,
  DigitalOcean Spaces, iDrive e2 and more.
* **Azure Blob Storage** - Store backups in a Microsoft Azure Blob container.
* **Google Cloud Storage** - Store backups in a Google Cloud Storage bucket.
* **WebDAV** - Store backups on any WebDAV-compatible server.

Key Features
============
* **Scheduled backups** - Ready-made daily, weekly and monthly cron jobs, all
  reachable from a *Schedule Actions* smart button on the configuration form.
* **Backup Now** - Run a manual backup for a configuration at any time from the
  form header, independent of the scheduled actions.
* **Download Backup** - Generate and download a fresh backup file directly from
  the browser without opening the database manager.
* **Multi-database backup** - Choose the backup scope per configuration: the
  current database, all databases on the server, or a hand-picked selection.
* **Backup formats** - Take full backups (with filestore, ``.zip``) or
  dump-only backups (``.dump``).
* **Automatic cleanup** - Automatically remove backups older than a configured
  number of days to keep destinations tidy.
* **Backup history** - Every run is logged with database name, destination,
  status, duration and message, viewable through a *History* smart button and a
  dedicated menu.
* **Last-run status** - The configuration shows the last backup date, its
  outcome and the last successful backup date at a glance.
* **Email notifications** - Get notified by email on every run or only on
  failures, with dedicated success and failure mail templates.
* **Connection testing** - Test the connection to each destination before
  saving, so credentials and endpoints are validated up front.
* **Systray indicator** - A backend systray widget surfaces recent backup
  status without leaving your current screen.
* **Secure master password handling** - The master password is validated but
  never persisted; automatic backups run without needing it stored.
* **Access control** - Backup configuration and history are restricted to a
  dedicated *Manager* group; the menus live in Settings after the Technical
  menu.

Required Python Packages
========================
Depending on the destinations you use, install the matching packages::

    pip3 install dropbox
    pip3 install pyncclient
    pip3 install boto3
    pip3 install nextcloud-api-wrapper
    pip3 install paramiko
    pip3 install azure-storage-blob
    pip3 install google-cloud-storage
    pip3 install webdavclient3

Configuration
=============
- www.odoo.com/documentation/19.0/setup/install.html
- Install our custom addon

License
-------
General Public License, Version 3 (LGPL v3).
(https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

Credits
-------
* Developers : (v15) Midilaj,
               (v16) Midilaj,
               (v16 Amazon S3,NextCloud) Anfas Faisal K,
               (v17) Aslam A K,
               (v18) Aslam A K,
               (v19) Ashwin A
  Contact : odoo@cybrosys.com

Contacts
--------
* Mail Contact : odoo@cybrosys.com

Bug Tracker
-----------
Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__

Further information
===================
HTML Description: `<static/description/index.html>`__