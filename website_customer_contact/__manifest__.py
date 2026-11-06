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
    'name': "Website Customer Contact",
    'version': '20.0.1.0.0',
    'category': 'Website',
    'summary': """Create and manage contacts and addresses from the website.""",
    'description': """This module enables the creation and management of contacts and addresses directly 
     from the website. Users can create, view, and edit contact details and associated addresses through 
     the website interface.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['portal', 'website'],
    'data': [
        'data/portal_entry_data.xml',
        'views/portal_templates.xml',
        'views/website_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_customer_contact/static/src/css/website_customer_contact.css',
            'website_customer_contact/static/src/js/customer_contact_edit_form.js',
            'website_customer_contact/static/src/js/customer_contact_form.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
