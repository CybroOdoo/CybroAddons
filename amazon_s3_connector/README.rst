.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community-1ABC9C.svg
    :alt: Community Edition

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |maintainer|

Odoo Amazon S3 Connector
========================

This module lets you browse, search and download the files of an Amazon S3
bucket from a dashboard in Odoo, and upload new files to it.

Key Features
------------

* Direct integration with Amazon S3 Cloud Storage from Odoo.
* View and manage files in the Amazon S3 bucket using a dedicated dashboard.
* Upload files directly to S3 with an upload wizard.
* Categorize, filter, and search files (PDF, Images, ZIP, Text, Excel).
* Secure credential configuration in Odoo General Settings.

Installation
------------
The module requires the Python library `boto3`.
Install it via pip:

    pip install boto3

Configuration
-------------
1. Navigate to **General Settings** -> **Integrations**.
2. Enable the **Amazon S3 Cloud Storage** option.
3. Fill in the **Amazon S3 Access Key**, **Amazon S3 Secret Key** and **Amazon S3 Bucket Name**.
4. Save the settings.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com


This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__
