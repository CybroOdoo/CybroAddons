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
    'name': 'Cookie Consent Manager',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Manage and customize website cookie consent templates""",
    'description': """The Cookie Consent Manager allows website owners to
manage and customize their cookie consent templates.
With this module, you can create, modify, and display
customized cookie consent banners to comply with
data protection regulations and improve user
privacy on your Odoo website.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website'],
    'data': [
        'security/ir.access.csv',
        'views/res_config_settings_views.xml',
        'views/cookie_information_views.xml',
        'views/website_cookie_bar_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
