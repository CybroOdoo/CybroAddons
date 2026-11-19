# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Ora-Ai Website',
    'version': '20.0.1.0.0',
    'category': 'Website/eCommerce',
    'summary': """Ora AI Website, Voice Assistant, Voice Ordering, Vapi AI, AI Shopping Assistant, Website Voice Order, eCommerce Voice Assistant, Odoo20 eCommerce, Odoo20 Website""",
    'description': """
     Let the visitors of your shop order by voice. Choose an Ora-Ai voice
     assistant in the website settings: a microphone button appears on the
     shop page, the visitors talk with the assistant in their language, the
     products the assistant talks about are highlighted, and the ordered
     products are added to the cart, ready for the checkout.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['ora_ai_base', 'website', 'website_sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/templates.xml',
        'views/website_menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ora_ai_website/static/src/js/website_templates.js',
            'ora_ai_website/static/src/scss/website_template.scss',
        ],
        'web.assets_tests': [
            'ora_ai_website/static/tests/tours/ora_ai_website_tour.js',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
