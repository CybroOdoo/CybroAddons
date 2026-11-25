.. image:: https://img.shields.io/badge/license-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

ZKTeco Biometric Attendance (ADMS Push)
=======================================
ZKTeco biometric devices push attendance to Odoo over the ADMS/iclock protocol.

Configuration
=============
* **Direct IP Connection**:
  Navigate to **Attendances -> Biometric (ADMS) -> Devices**, create a new device, set **Connection Mode** to *Direct IP*, enter the **IP Address**, **Port** (default: 4370), and **Device Timezone**. Click **Test Connection** to test connectivity, then click **Synchronize** to fetch users and attendance records.

* **ADMS Push Mode**:
  On the biometric terminal, configure **Cloud Server Setting / ADMS** with your Odoo server host and port. In Odoo, open **Attendances -> Biometric (ADMS) -> Devices Pending Approval**, set the **Device Timezone**, and click **Approve Device**.

* **Device User & Employee Mapping**:
  Navigate to **Attendances -> Biometric (ADMS) -> Device Users** to map device PINs to Odoo employees, or generate employee **Badge IDs** and export employees to the biometric device.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Affero General Public License v3.0 (AGPL v3)
(https://www.gnu.org/licenses/agpl-3.0-standalone.html)

Credits
-------
* Developer : (V19) Nisarudheen M, Nivedhya T, Chethana R
Contact: odoo@cybrosys.com

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

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
