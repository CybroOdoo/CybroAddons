.. image:: https://img.shields.io/badge/license-LGPL--3-green.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

Odoo Support Request
====================
Create Odoo Support Request To Cybrosys

Overview
========
Adds a "Contact Cybrosys Support" tool to the Odoo backend. A headphones icon
appears in the systray (and an entry in the user menu); clicking it — or
pressing ``Alt+Shift+H`` — opens a wizard where any internal user can raise a
support request to Cybrosys without leaving Odoo.

The wizard collects the customer name, email, phone, subject, description,
support type, category and priority, and lets the user attach files. A live
"Show what will be sent" preview displays the exact JSON payload (with
attachment bytes redacted) before submitting.

Two ways to send:

* **Submit** – POSTs the request as JSON to the Cybrosys support server. On
  success a sticky notification shows the created ticket reference
  (``CYB-…``). Errors are reported clearly (attachments too large, service
  unavailable, network problems, etc.).
* **WhatsApp** – opens a WhatsApp chat pre-filled with the request details.

The Submit path sends your request securely to the Cybrosys support system,
where it becomes a support ticket the Cybrosys team works on. You receive a
ticket reference to follow up with.

Features
========
* Systray icon + user-menu entry, with an ``Alt+Shift+H`` keyboard shortcut.
* Transient wizard (``client.support``) – no data stored locally.
* Support type, category and priority selection.
* Multiple file attachments (sent inline, base64-encoded).
* Payload preview before sending.
* WhatsApp fallback channel.
* Robust, user-friendly error handling on submission.

Data privacy
============
When you click **Submit**, this module sends the details you entered — name,
email, phone, subject, description and any files you attach — to the Cybrosys
support server over HTTPS, so that a support ticket can be created for you.

* Nothing leaves your database unless a user explicitly clicks **Submit** (or
  **WhatsApp**). The module does not run in the background or transmit any data
  on its own.
* Only authenticated internal users can open the support wizard.
* Use the **Show what will be sent** preview to review the exact data before
  submitting.
* The destination server is configurable (see *Configuration*); by default it
  is the official Cybrosys support server.

Configuration
=============
The support server URL is stored in a system parameter, so a change of domain
is a config edit rather than a code release:

* **Settings → Technical → System Parameters**
* Key: ``cybrosys_support_client.endpoint_url``
* Default: ``https://support.cybrosys.com/help/request``

If the parameter is missing or blank, the module falls back to the default
above.

License
=======
GNU LESSER GENERAL PUBLIC LICENSE v3.0 (LGPL v3)
(https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : http://www.cybrosys.com

Bug Tracker
-----------
Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.
For support and more information, please visit https://www.cybrosys.com

Further information
===================
HTML Description: `<static/description/index.html>`__
