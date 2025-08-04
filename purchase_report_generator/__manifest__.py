# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.info)
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
##############################################################################
{
    'name': 'Purchase All In One Report Generator',
    'version': '18.0.1.0.0',
    'category': 'Purchases',
    'summary': """This module Helps to Generate All in One Dynamic Purchase
    Report.""",
    'description': """This module facilitates comprehensive Purchase Reports, 
    offering insights into a company's procurement analysis from various 
    angles, including orders, order details, sales representatives, and the 
    ability to filter data by different date ranges.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/dynamic_purchase_report_views.xml',
        'report/purchase_order_report_templates.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'purchase_report_generator/static/src/css/purchase_report.css',
            'purchase_report_generator/static/src/js/purchase_report.js',
            'purchase_report_generator/static/src/xml/purchase_report_view.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
