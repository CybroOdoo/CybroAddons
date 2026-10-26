.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |maintainer|

Direct Print
============
* Direct Print connects Odoo to PrintNode cloud printing service.


Key Features
------------

* Direct printing of Odoo reports via PrintNode cloud service.
* Seamless connection between Odoo and PrintNode API.
* Support for single and multiple printer configurations.
* Automatic document dispatch to selected printers upon report generation.

Installation
------------
* External dependency "printnodeapi" is required.

Configuration
-------------
First you need to install the PrintNode application.
 * Go to https://www.printnode.com/en/download
 * Click on the download button for your operating system.
 * Install the PrintNode application.
After that, generate an API key from your PrintNode account.
After installing this module, configure your API key in Settings and check available printers.
When you click the print button on a document, it will automatically send the print job to the selected printer(s) and download the file.
When running the module on localhost, ensure network access to the PrintNode API is permitted.

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
