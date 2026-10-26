.. |license| image:: https://img.shields.io/badge/license-LGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. |odoo| image:: https://img.shields.io/badge/Odoo-20.0-875A7B.svg
    :target: https://www.odoo.com
    :alt: Odoo 20.0

.. |edition| image:: https://img.shields.io/badge/Edition-Community%20%7C%20Enterprise-1ABC9C.svg
    :alt: Community and Enterprise Editions

.. |maintainer| image:: https://img.shields.io/badge/maintainer-Cybrosys-875A7B.svg
    :target: https://cybrosys.com
    :alt: Maintainer: Cybrosys Techno Solutions

|license| |odoo| |edition| |maintainer|

Generate Product Images Using OpenAI
====================================

This module generates images for products using OpenAI (``gpt-image-2``).

Key Features
------------

* Generate product images from a free-text prompt.
* Choose the number of images (1 to 4), the resolution, and the quality.
* Keep a history of the generated images for each product template.
* Set any generated image as the main product image with **Set as Product Image**.
* Only users in the Product **Administrator** group can generate images; other internal users can only view the history.
* The last generated image is also set as the main product image (``image_1920``) immediately.

Installation
------------

This module requires the ``openai`` Python library:

* ``pip install openai``

Configuration
-------------

* Go to **Settings > General Settings > Integrations > OpenAI** and enter the OpenAI API key (provided by the *OpenAI Odoo Base* module).
* Users who generate images need the Product **Administrator** access right.

Usage
-----

1. Go to **Inventory > Products > Products** or **Sales > Products > Products**.
2. Open a product template or select a product from the list view.
3. Click the **Action** gear icon and select **Generate Image Using OpenAI**.
4. Enter a descriptive image prompt, select the number of images, resolution, and quality, then click **Generate Images**.
5. Generated images are saved in history and accessible via the **AI Images** smart button on the product template.
6. Open any record in the AI Images list and click **Set as Product Image** to apply it as the product's primary picture.

Company
-------

* `Cybrosys Techno Solutions <https://cybrosys.com/>`__

License
-------

Lesser General Public License, Version 3 (LGPL v3).
(http://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
-------

* Developers:

  * (V18) Manasa T P
  * (V19) Fansa Jabeen A
  * (V20) Cybrosys Techno Solutions

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
