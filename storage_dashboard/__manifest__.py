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
    'name': 'Storage Dashboard',
    'version': '20.0.1.0.0',
    'category': 'Technical',
    'summary': 'See the storage used by the models of your database and the memory usage of the server on one dashboard.',
    'description': """
        The Memory Usage dashboard in Settings shows the server memory and
        CPU usage, the Odoo memory and time limits, the database details
        and a chart of the models using the most storage.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'web'],
    'data': [
        'security/ir.access.csv',
        'views/storage_dashboard_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'storage_dashboard/static/src/js/storage_dashboard.js',
            'storage_dashboard/static/src/xml/storage_dashboard_templates.xml',
            'storage_dashboard/static/src/scss/storage_dashboard.scss',
        ],
        'web.assets_tests': [
            'storage_dashboard/static/tests/tours/storage_dashboard_tour.js',
        ],
    },
    'external_dependencies': {'python': ['psutil']},
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
