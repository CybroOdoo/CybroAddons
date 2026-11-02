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

Warehouse 3D Map & Designer
===========================

Design warehouse layouts visually on an interactive 2D canvas and explore them
in a 3D WebGL walkthrough. Drag and drop racks, shelves, bins and zones onto a
grid, see how full each location is with a stock density heatmap, and search
for a product to fly the 3D camera straight to where it is stored.

Key Features
------------

* 2D drag-and-drop canvas designer with grid snapping
* 3D WebGL warehouse walkthrough with shelf rows, shadows and labels
* On-screen pan, rotate, zoom and reset camera controls in 3D
* Real-time stock density heatmap, from green (empty) to red (full)
* Product search by name or internal reference, with the 3D camera zooming to
  the location holding the most stock
* One layout per floor, with a floor switcher and a stacked all-floors 3D view
* Location shapes (Rack, Shelf, Bin, Zone, Dock, Floor Area, Packing,
  Cold Room, QC Area) and custom colours
* Wall and room map objects
* Location detail sidebar with size, rows and colour
* Read-only Warehouse Map for users without manager rights
* Focus mode and keyboard shortcuts
* Export and import of layouts as XML, restoring locations and replacing the
  map objects of the imported layouts
* Multi-company compatible
* Works with both Community and Enterprise editions

Installation
------------
No external dependencies. The module depends on Web (``web``) and Inventory
(``stock``), and the three.js library used for the 3D view is bundled with the
module.

Configuration
-------------
No additional configuration is required.

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
