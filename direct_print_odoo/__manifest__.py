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
    'name': 'Direct Print',
    'version': '20.0.1.0.0',
    'category': 'Extra tools',
    'summary': 'The Direct Print is a tool that connects Odoo to PrintNode, '
               'a cloud-based printing service. This connector allows users to'
               ' send print jobs from their Odoo environment to any printer '
               'connected to their PrintNode account.',
    'description': 'PrintNode is a cloud-based printing service that enables '
                   'businesses to print documents remotely from any device or '
                   'location. The Direct Print for Odoo is a '
                   'software module that integrates Odoo, an open-source ERP '
                   'system, with PrintNode printing capabilities.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_setup'],
    'data': [
        'security/ir.access.csv',
        'views/res_config_settings_views.xml',
    ],
    "external_dependencies": {
        'python': ['printnodeapi']
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
