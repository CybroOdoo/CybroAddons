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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Inventory Stock Dashboard',
    'version': '20.0.1.0.0',
    'category': 'Warehouse',
    'summary': 'Detailed dashboard view for Inventory module.',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',  # pylint: disable=manifest-required-author
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['stock'],
    'data': [
        'data/ir_config_parameter_data.xml',
        'views/res_config_settings_views.xml',
        'views/dashboard_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'inventory_stock_dashboard_odoo/static/lib/chartjs/chart.umd.js',
            'inventory_stock_dashboard_odoo/static/src/css/dashboard.css',
            'inventory_stock_dashboard_odoo/static/src/js/dashboard.js',
            'inventory_stock_dashboard_odoo/static/src/xml/inventory_dashboard_template.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
