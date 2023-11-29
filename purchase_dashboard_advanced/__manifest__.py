# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Purchase Dashboard",
    'version': '15.0.1.0.0',
    'category': 'Purchases',
    'summary': "Elevate your financial awareness with our comprehensive "
               "Purchase Analysis Dashboard",
    'description': "Empower your financial insights with our all-in-one "
                   "Purchase Analysis Dashboard. Effortlessly track and "
                   "evaluate purchase expenditures on a monthly and yearly "
                   "basis, identify top and priority products, and stay "
                   "informed about upcoming purchase details",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['purchase'],
    'data': [
        'views/purchase_dashboard_menus.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'purchase_dashboard_advanced/static/src/js/dashboard.js',
            'purchase_dashboard_advanced/static/src/css/style.css',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.bundle.js',
        ],
        'web.assets_qweb': [
            'purchase_dashboard_advanced/static/src/xml/purchase_dashboard_templates.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
