# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Inventory Dashboard Odoo 16',
    'version': '16.0.1.0.1',
    'category': 'Inventory',
    'summary': 'Inventory Dashboard',
    'description': "Detailed Dashboard View For Inventory",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['stock', 'base'],
    'data': ['views/style.xml',
             'views/dashboard_menus.xml',
             'views/res_config_settings_views.xml',
             ],
    'assets': {
        'web.assets_backend': [
            'inventory_stock_dashboard_odoo/static/src/css/dashboard.css',
            'inventory_stock_dashboard_odoo/static/src/js/dashboard.js',
            'inventory_stock_dashboard_odoo/static/src/js/lib/Chart.bundle.js',
            'inventory_stock_dashboard_odoo/static/src/xml/dashboard.xml'
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
