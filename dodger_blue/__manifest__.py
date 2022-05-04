# -*- coding: utf-8 -*-

{
    "name": "Dodger Blue Backend Theme",
    "summary": "Outrageous Blue Backend Theme",
    "version": "14.0.1.0.0",
    "category": "Themes/Backend",
    "website": "https://github.com/Frontware/CybroAddons",
    "description": """Backend theme for Odoo 14.0 community edition. Blue theme blue backend theme odoo backend theme""",
    'author': 'Frontware, Cybrosys Techno Solutions',
    'company': 'Frontware, Cybrosys Techno Solutions',
    'maintainer': 'Frontware, Cybrosys Techno Solutions',
    "depends": [
        'website',
        'portal',
        'web_responsive'
    ],
    "data": [
        'views/assets.xml',
        'views/login_templates.xml',
    ],
    'qweb': ['static/src/xml/base_ext.xml',
             # 'static/src/xml/sidebar_menu_icon.xml',
             'static/src/xml/*.xml'],
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,

}
