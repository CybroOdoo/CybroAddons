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

Theme Nutivo
============

A refined eCommerce theme for premium nuts, dates, dried fruits and gift
hampers: ivory, forest green and gold, with soft motion, ready-made pages and a
shop built around pack sizes. It works with the standard Odoo header, shop and
website builder, so every builder option keeps working.

Key Features
------------

* Complete store design: announcement bar, header, footer and ready-made Home,
  Our Story and Contact pages.
* Shop mega menu that lists up to four shop categories and a gifting feature
  card, editable in the website builder.
* Product cards with the pack sizes of each product as chips, a +N popover for
  the remaining sizes, ratings, ribbons and an Add button.
* Quick view with all the options, add-ons and custom text of a product.
* Bag and wishlist drawers with a free shipping meter and suggested products.
* Standard eCommerce shop with price, rating and highlight filters, category
  rail, sorting and a grid or list switch.
* Twenty-one editable Nutivo blocks in the website builder.
* Smooth scrolling and scroll animations.
* Responsive layout for phone, tablet and desktop.

Installation
------------
Depends on Website Sale and Website Mass Mailing (newsletter forms). No external
dependencies.

Configuration
-------------
* Install the theme from Website > Configuration > Settings > Choose a Theme
  (or the theme selector of the website builder). The Home, Our Story and
  Contact pages, the menu, the header with its Shop mega menu, the footer and
  the logo are set up automatically.
* No product, category or review is created: the shop shows the data of your
  website.

  * The Shop mega menu, the category row of the shop and the footer links use
    the top level public categories that have published products. Name them
    Nuts, Dates & Dried Fruits, Trail Mixes and Gift Hampers to have the footer
    links point at them.
  * The pack sizes of the product cards are the variants of each product
    (e.g. a "Pack size" attribute with 250g, 500g and 1kg values).
  * The badges of the cards are the product ribbons; they are also the
    Highlights filter of the shop. Ratings come from the customer reviews.
* The bag drawer shows a free shipping meter. Its threshold is the system
  parameter ``theme_nutivo.free_shipping_amount`` (999 by default, in the
  website currency); set it to 0 to hide the meter.
* The Nutivo blocks are in the Nutivo group of the website builder. The
  Bestsellers and Gift Hampers blocks show the shop products live.
* The text, the addresses and the images are samples: replace them from the
  website builder. The animations use GSAP and Lenis, bundled with the theme.

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
