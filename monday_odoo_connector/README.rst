.. image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

Monday.com Odoo Connector
=========================
This module helps to import data from Monday.com to Odoo. It imports Users,
Boards, Groups, Items and Customers using the Monday.com API. The import is
one-way (Monday.com to Odoo) and can be repeated: existing boards, groups and
items are updated instead of duplicated.

Installation
------------
The Python library ``requests`` must be installed (``pip install requests``).

Configuration
-------------
First you need to create a Monday.com API token.

1. Log in to your Monday.com account.
2. Click on your profile picture at the top right corner.
3. Click on Developers.
4. Open the API token section and copy your personal API token.
5. In Odoo, go to Monday > Configuration > Credentials, create a credential
   with the token and use the Test Connection button to verify it.

Usage
-----
Go to Monday > Configuration > Connector, select the credential and choose
what to import: Users, Boards (with their groups and items) and Customers
(from the board named Contacts). Users are created without a password as
portal users; they must use the password reset flow to log in. The module is
available to administrators only.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
GNU Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------
* Developers:

  * (V16) Unnimaya C O
  * (V17) Kailas Krishna
  * (V18) Ammu Raj
  * (V19) Anjali VP

* Contact: odoo@cybrosys.com

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Maintainer
----------
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__

Further information
-------------------
HTML Description: `<static/description/index.html>`__
