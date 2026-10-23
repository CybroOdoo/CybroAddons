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

Login using QR Code
===================

This module allows internal users to seamlessly and securely authenticate and log in to Odoo by scanning a generated QR code with their camera or webcam.

Key Features
------------

* Instant login for internal users by scanning a unique QR code.
* Automatic generation of secure, cryptographically random QR tokens per user.
* Ability to regenerate and revoke QR tokens directly from the user profile.
* Built-in webcam/camera QR scanner overlay directly on the Odoo login page.
* Fully client-side QR scanning powered by bundled local jsQR library.

Installation
------------
* External Python dependency: ``qrcode`` (``pip install qrcode``)

Configuration
-------------
No additional configuration is required.

Security Note
-------------
The QR code is equivalent to a password. Anyone who obtains the image can log in
as that user (users with two-factor authentication enabled are excluded).
Only administrators can view it; regenerate it if it is exposed.

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
