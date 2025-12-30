# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Sales Dashboard",
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Detailed dashboard view for Sales module.',
    'description': """This module provides a comprehensive dashboard for the Sales module, 
    offering a clear and actionable overview of orders, quotations, invoicing status, 
    revenues, and customer behavior. It enables sales teams and managers to monitor performance, 
    identify trends, and make informed decisions with real-time data visibility.""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'sale_management', 'web'],
    'data': [
        'views/sales_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sales_management_dashboard/static/src/js/sales_dashboard.js',
            'sales_management_dashboard/static/src/xml/sales_dashboard.xml',
            'https://cdn.jsdelivr.net/npm/chart.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
