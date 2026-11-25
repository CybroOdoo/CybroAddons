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

Ora-AI Base
==========

Ora-AI Base integrates real-time AI voice assistant capabilities into Odoo 20 via the Vapi.ai platform. It connects Odoo with advanced LLMs (OpenAI, Anthropic Claude, Google Gemini, Groq), speech-to-text transcribers (Deepgram, Gladia), and ElevenLabs voice synthesis, allowing users to perform core business actions hands-free.

Key Features
------------

* **Voice-to-Order**: Place sales orders naturally through voice commands with customer verification, variant handling, and optional auto-confirmation.
* **Customer & Invoicing**: Register new customer contacts and generate draft customer invoices hands-free.
* **Product Creation**: Add new products and SKUs directly to the catalog using voice commands.
* **RAG Knowledge Base**: Upload custom documents (PDF, DOCX, CSV up to 25MB) synced to Vapi for domain-specific, grounded business answers.
* **Systray Voice Access**: Launch voice sessions instantly from the Odoo top navbar with live soundwaves and real-time WebSocket order streaming.
* **Call Audit & History**: Automatically log duration, external costs, audio recordings, and full conversation transcripts linked to created records.
* **Multi-LLM & Multilingual**: Choose across leading AI and transcriber models with dynamic multilingual voice switching.

Installation
------------

Install the required Python package:

```bash
pip install googletrans
```

Configuration
-------------

1. Navigate to **Voice Assistant > Configuration > Settings**.
2. Enter your **Private API Key** and **Public API Key** from the [Vapi Dashboard](https://dashboard.vapi.ai/api-keys).
3. Create and configure your assistant under **Voice Assistant > Assistants** and launch it from the top systray.

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
