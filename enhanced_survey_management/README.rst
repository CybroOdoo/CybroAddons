.. image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0.en.html
    :alt: License: LGPL-3

Enhanced Survey Management
==========================
Enhances Odoo Surveys with additional question types, custom matrix options, dynamic model selection, attendee file uploads, portal response history, and XLSX report export.

Installation
------------
* https://www.odoo.com/documentation/20.0/administration/on_premise.html
* Install the ``xlsxwriter`` Python package (automatically declared in ``external_dependencies``).
* Install the ``enhanced_survey_management`` custom addon.

Usage
-----
* Navigate to **Surveys > Surveys**, open or create a survey, and click **Add a question** to select custom question types (Time, Month, Name, Address, Email, Password, QR Code, URL, Week, Color, Range, Many2one, Upload File, Many2many, Selection, Barcode) or choose **Custom Matrix** on a Matrix question.
* Enable **Portal Visibility** on the **Options** tab to expose attendee response history in the customer portal (``/my/survey/ans``), or set **Access Mode** to **Website** to list the survey at ``/public/survey``.
* Click **Print XLSX** in the survey form header to export survey responses as an Excel workbook.

License
-------
GNU Lesser General Public License v3.0 (LGPL-3)
(https://www.gnu.org/licenses/lgpl-3.0.en.html)

Company
-------
* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

Credits
-------
* Developers: (V16) Mohammed Savad, Ahammed Harshad, Gee Paul Joby, Nihala Jebin,
              (V17) Nihala KP,
              (V19) Prasudhi A,
              (V20) Cybrosys Techno Solutions

Contact: odoo@cybrosys.com

Contacts
--------
* Mail Contact: odoo@cybrosys.com
* Website: https://cybrosys.com

Bug Tracker
-----------
Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Maintainer
----------
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit https://www.cybrosys.com

Further information
-------------------
HTML Description: `<static/description/index.html>`__
