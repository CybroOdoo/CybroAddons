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

Product Recommendation AI
=========================

AI-powered product recommendations with multiple performance options.

Key Features
------------

* Order-Based Recommendations
* AI Semantic Matching
* Product Carousel Display
* Configurable Recommendation Mode
* Metadata Selection Control

Installation
------------
Python: ``numpy`` (``pip install numpy``).

The Accurate model calls the Nomic embedding API and needs nothing else. The
Fast model computes the embeddings on the server with MiniLM, and needs the
optional ``sentence-transformers`` library, which installs ``torch``::

    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install sentence-transformers

Configuration
-------------
With the Fast model, give the Odoo workers enough memory for the model in the
Odoo configuration file (odoo.conf):

* ``limit_memory_hard = 4096000000``
* ``limit_memory_soft = 3072000000``

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

