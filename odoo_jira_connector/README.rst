.. image:: https://img.shields.io/badge/license-LGPL--3-green.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

Odoo Jira Connector
===================
Odoo Jira Connector synchronizes projects, tasks, comments, attachments and
users between Odoo and Jira Cloud, so teams that use both tools work on the
same data.

Configuration
=============
* Go to Project > Configuration > Settings and fill in the Jira URL, the email
  address of your Atlassian account (User Name) and an API token, then click
  Test Connection.
* To receive Jira changes in real time, enable Automatic and create a Jira
  webhook pointing to your Odoo address followed by ``/jira_webhook``
  (HTTPS only). Enter a secret on the Jira webhook and enter the same value in
  Webhook Secret. Webhook calls without a configured secret and valid HMAC
  signature are rejected.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
GNU Lesser General Public License, Version 3 (LGPL v3).
https://www.gnu.org/licenses/lgpl-3.0-standalone.html

Credits
-------
* Developers: (V17) Dhanya B, (V18) Javid A, (V19) Harshitha AP
* Contact: odoo@cybrosys.com

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
