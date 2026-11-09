.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
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

Hide Any Menu User Wise
========================
* Hide Any Menu User Wise

This module provides functionality to hide or restrict menu items on a
per-user or per-group basis in Odoo. Administrators can control which menus
each user is allowed to see, so users only have access to the relevant parts
of the system, improving both security and usability. System administrators
are never restricted and always keep the full menu.

It also lets administrators set the order of the apps for each team, lets
users arrange their own apps, and gives everyone a Favourites menu in the
navbar to reach the menus they use most.

Key Features
--------
* Hide any menu or sub-menu for a specific user.
* Restrict a menu for an entire user group at once.
* System administrators are never restricted and always see every menu.
* Manage all menu restrictions from one central screen under
  Settings > Users & Companies.
* Copy one user's hidden menus onto other users in a single click.
* Cascade a menu's restrictions to all of its sub-menus.
* Hidden menus and restricted users stay in sync automatically.
* Menu Profiles: set the app order and shared shortcuts for groups or users.
* Arrange My Apps: users reorder their own apps and can reset to the team
  order.
* Favourite Menus: star any menu from the navbar, search every visible menu,
  and see the team shortcuts. Hidden menus never appear.
* Compatible with Odoo 20 Community and Enterprise editions.

Installation
------------
No external dependencies.

Configuration
-------------
* No additional configuration is required. Once installed, open a user under
  Settings > Users & Companies > Users and use the "Hide Specific Menu" tab to
  select the menus to hide for that user.
* To restrict menus by user or group directly, open the menu item and use the
  "Restrict Access" tab.
* Use Settings > Users & Companies > Menu Management > Menu Restrictions to
  review and manage all restrictions in one place, and the "Copy Hidden Menus"
  wizard to apply a user's hidden menus to other users.
* Use Settings > Users & Companies > Menu Management > Menu Profiles to set the
  app order and team shortcuts for groups or users. A profile without groups
  and users applies to everyone; each user gets the first matching profile.
* Users open "Arrange My Apps" from their user menu (top-right avatar) to set
  a personal app order, and the star icon in the navbar to manage favourites.

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------
Lesser General Public License, Version 3 (LGPL v3).
(https://www.gnu.org/licenses/agpl-3.0-standalone.html)

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
