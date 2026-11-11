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

AI Address Autofill
==================
Extract and parse full addresses into structured contact fields (Street, Street 2, City, State, ZIP, and Country) using Google Gemini AI and the official Google GenAI Python SDK.

Key Features
------------
* **Intelligent AI Address Parsing**: Automatically parses unstructured, multi-line, or messy single-string addresses into discrete Odoo contact fields (Street, Street 2, City, State, ZIP Code, and Country) using Google Gemini AI.
* **Dual Access Points**: Conveniently trigger Address Autofill directly from the **Contact Form View** header button or from the **Contacts List View** Actions (Cog) menu.
* **Interactive 2-Step Review Wizard**: Paste raw text in the draft state, review and adjust parsed address fields in the extracted state, and confirm before applying.
* **Selective Overwrite Protection**: Choose whether to overwrite existing contact address fields or preserve existing data and only populate missing information.
* **New Contact Creation**: Easily generate a brand-new contact directly from raw address text or apply the extracted fields to an existing contact.
* **Built-in Connection Testing**: Validate Gemini API credentials and model accessibility in real-time with a dedicated "Test Connection" button.

Installation
------------
1. Install the required Python library:

.. code-block:: bash

    pip install google-genai


Configuration
-------------
1. Log into Odoo as an Administrator.
2. Navigate to **Contacts > Configuration > Settings** (or **Settings > General Settings > AI Address Autofill**).
3. In the **Google Gemini AI** section:
   - **Gemini API Key**: Enter your API key obtained from `Google AI Studio <https://aistudio.google.com/app/apikey>`_.
   - **Gemini Model**: Select your preferred model (e.g., *Gemini 3.5 Flash*, *Gemini 3.8 Flash*, or *Gemini 3.5 Flash Lite*).
   - Click **Test Connection** to confirm connectivity with the Google Gemini API.
4. In the **Address Autofill** section:
   - Enable the **Address Autofill** checkbox to activate autofill actions across Contact form and list views.
5. Click **Save**.

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

Further information
===================
HTML Description: `<static/description/index.html>`__
