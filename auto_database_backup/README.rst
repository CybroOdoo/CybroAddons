.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community-1ABC9C.svg
    :alt: Community Edition

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |maintainer|

Automatic Database Backup
================

Automatic Database Backup allows users to schedule and generate database and
filestore backups automatically and store them across multiple local and cloud
storage destinations. Users can configure a backup destination, test the
connection, and run backups daily, weekly, or monthly. Backups can also be
generated manually or downloaded directly from the backup configuration.

Key Features
------------

* Automatically schedule database and filestore backups.
* Store backups on a Local Server.
* Upload backups to FTP servers.
* Upload backups securely through SFTP.
* Store backups in Google Drive.
* Store backups in Dropbox.
* Upload backups to Microsoft OneDrive.
* Store backups on Nextcloud servers.
* Upload backups to Amazon S3 buckets.
* Support S3-compatible storage providers using custom endpoint URLs.
* Support providers such as Backblaze B2, Wasabi, Cloudflare R2, MinIO,
  DigitalOcean Spaces, and iDrive e2.
* Store backups in Microsoft Azure Blob Storage.
* Upload backups to Google Cloud Storage.
* Store backups on WebDAV-compatible servers.
* Configure daily, weekly, and monthly scheduled backup actions.
* Access scheduled actions through the Schedule Actions smart button.
* Generate backups manually using the Backup Now option.
* Download a freshly generated backup directly from the configuration form.
* Configure backups for the current database, all databases, or selected
  databases.
* Generate full backups including the filestore in `.zip` format.
* Generate database-only backups in `.dump` format.
* Automatically remove backups older than the configured retention period.
* Maintain backup history with database name, destination, status, duration,
  and execution messages.
* View backup history through the History smart button and dedicated menu.
* Display the last backup date, status, and last successful backup date.
* Send email notifications for every backup or only when a backup fails.
* Test destination connections before saving the configuration.
* Display recent backup status through a backend systray indicator.
* Validate the master password without permanently storing it.
* Restrict backup configuration and history access to authorized Manager users.

Installation
-------------

Install the required Python packages depending on the backup destinations used::

pip3 install dropbox
pip3 install pyncclient
pip3 install boto3
pip3 install nextcloud-api-wrapper
pip3 install paramiko
pip3 install azure-storage-blob
pip3 install google-cloud-storage
pip3 install webdavclient3


Install the module in the Odoo Apps menu after adding it to the Odoo addons path.

Configuration
-------------

Configure a backup destination from the backup configuration menu and provide
the required credentials and connection details.

The module supports Local Server, FTP, SFTP, Google Drive, Dropbox, Microsoft
OneDrive, Nextcloud, Amazon S3, S3-compatible storage, Azure Blob Storage,
Google Cloud Storage, and WebDAV.

Use the connection testing option to validate the destination before running
scheduled backups.

Company
-------------

* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------------

Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------------

* Developers :
  (v15) Midilaj,
  (v16) Midilaj,
  (v16 Amazon S3, Nextcloud) Anfas Faisal K,
  (v17) Aslam A K,
  (v18) Aslam A K,
  (v19) Ashwin A,
  (v20) Vignesh K

Contacts
-------------

* Mail Contact : [odoo@cybrosys.com](mailto:odoo@cybrosys.com)
* Website : https://cybrosys.com

Maintainer
-------------

.. image:: https://cybrosys.com/images/logo.png
:target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__
