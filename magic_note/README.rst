.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

Magic Note
===========
This module aims to automatically update the color of the notes/memo
in organizer tab under messaging menu.

Installation
============
- www.odoo.com/documentation/14.0/setup/install.html
- Install our custom addon

Features
========
* set a name for the category of coloured notes
* Select color from a pre defined list of colors
* Select a range of date limit(days) in integer form
* Updates the note's color in on-load of kanban view

note:

    By default on installation of this module it creates
    a field called dead date and sets it to the current date

    A new tab is created under settings-configuration where
    >set default color when no date intervals are defined
    >set color when any record doesn't come under date intervals
    >set color for notes which exceed the deadline date

FormView

    * select a name which is not compulsory set lower and upper limit of days
    * Select the color

ListView
    * shows you the defied color and days(interval)

Company
=======
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
=======
GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3)
(https://www.gnu.org/licenses/agpl-3.0-standalone.html)

Credits
=======
* Developer: (V14) RAHUL C K, Contact: odoo@cybrosys.com

Contacts
=======
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Bug Tracker
===========
Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit https://www.cybrosys.com.

Further information
===================
HTML Description: `<static/description/index.html>`__
