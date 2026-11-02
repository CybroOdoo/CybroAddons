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
    'name': 'WhatsApp Product Inquiry In Website',
    'version': '20.0.1.0.0',
    'category': 'eCommerce',
    'summary': """WhatsApp Product Inquiry, WhatsApp Inquiry Button, eCommerce WhatsApp, Website WhatsApp, Product Inquiry, Odoo WhatsApp, Odoo20 eCommerce, Odoo20 Website""",
    'description': """
     Add a WhatsApp Inquire button next to Add to Cart on the product pages
     of the website. Clicking it opens WhatsApp with a message to the company
     WhatsApp number, containing the configured inquiry message and the link
     to the product. The number and the message are configured on the
     company, and the button only shows when a number is set.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website_sale'],
    'data': [
        'views/res_company_views.xml',
        'views/website_sale_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'whatsapp_product_inquiry/static/src/css/style.css',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
