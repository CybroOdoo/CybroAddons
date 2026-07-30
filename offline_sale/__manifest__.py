# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'Offline Sales',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Offline-first sales management for high volume and offline capability',
    'description': """This module provides an offline-first sales management solution for Odoo,
     allowing users to continue creating and managing sales orders even when
     internet connectivity is unavailable or unstable.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'product', 'web', 'auth_totp'],
    'data': [
        'security/ir.model.access.csv',
        'views/offline_sale_menus.xml',
        'views/offline_sale_assets.xml',
        'views/sale_order_views.xml',
        'views/login_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
             'offline_sale/static/src/css/fonts.css',
             'offline_sale/static/src/js/main_backend_handler.js',
             'offline_sale/static/src/js/systray_offline_button.js',
             'offline_sale/static/src/xml/systray_offline_button.xml',
        ],
        'offline_sale.assets': [
            'offline_sale/static/src/app/css/main.css',
            'offline_sale/static/src/app/js/offline_sale_app.js',
            'offline_sale/static/src/app/js/main.js',
            'offline_sale/static/src/app/xml/main.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
