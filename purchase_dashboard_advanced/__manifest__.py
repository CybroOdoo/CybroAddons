# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
{
    'name': "Advanced Purchase Dashboard",
    'version': '17.0.1.0.0',
    'category': 'Purchases',
    'summary': 'The Purchase Dashboard provides a detailed overview of your '
               'purchases in a single screen',
    'description': 'A dashboard for keeping track and evaluate various '
                   'aspects of spending on purchases',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['purchase'],
    'data': [
        'views/purchase_dashboard_advanced_menus.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'purchase_dashboard_advanced/static/src/xml/*.xml',
            'purchase_dashboard_advanced/static/src/js/*.js',
            'purchase_dashboard_advanced/static/src/css/style.css',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.bundle.js'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
