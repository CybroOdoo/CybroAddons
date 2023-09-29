.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

POS Birthday Discount
=====================

This module aims in providing special discount for customers in POS on their respective birthdate.

Installation
============

- www.odoo.com/documentation/16.0/setup/install.html
- Install our custom addon

Configuration
=============

* After installing the module, go to 'Point of Sale' module settings. Under 'Pricing' section enable the field
  'Birthday Discount' and set the percentage of discount.
* Enable the 'Only Apply the discount on the first order on Birthday' field to apply discount only for the first order
  of customer birthday. Save settings.
* Set the customer birthday in the contact form.( A new field 'Birth Date' will be found )
* Open POS session
* Create order for the customers and the discount configured in the settings will be automatically applied to the
  products if the current date is the birthdate of customer.

Features
========

* Special discount for products in POS on customer birthday.
* Discount can be configured to apply only for first order on birthday.
* Discount will be automatically applied to products while creating pos order.
* Birthday greeting label will be shown near customer name in POS session.
* New field 'Birth Date' is added in customer form.

License
=======
GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3)
(https://www.gnu.org/licenses/agpl-3.0-standalone.html)

Credits
=======
Developer: (V16) Rahul C K, Contact: odoo@cybrosys.com

Contacts
--------
* Mail Contact : odoo@cybrosys.com
* Website : https://cybrosys.com

Bug Tracker
===========
Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Maintainer
----------
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit https://www.cybrosys.com.

Further information
===================
HTML Description: `<static/description/index.html>`__
