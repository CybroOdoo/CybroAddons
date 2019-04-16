# -*- coding: utf-8 -*-

{
    "name": "Outrageous Orange Backend Theme",
    "summary": "Outrageous Orange Backend Theme",
    "version": "12.0.1.0.0",
    "category": "Theme/Backend",
    "website": "https://www.cybrosys.com",
    "description": """Backend theme for Odoo 12.0 community edition.""",
    'images': ['static/description/banner.jpg'],
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    "installable": True,
    "depends": [
        'website',
        'portal',
        'web_responsive'
    ],
    "data": [
        'views/assets.xml',
        'views/login_templates.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
