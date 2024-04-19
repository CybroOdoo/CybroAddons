# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Ayana KP (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Sales All In One Report Generator',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': """This module Helps to Generate All in One Dynamic 
    Sale Report""",
    'description': """This module facilitates comprehensive Sale Reports, 
     offering insights into a company's procurement analysis from various 
     angles, including orders, order details, sales representatives, and the 
     ability to filter data by different date ranges.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'report/sale_order_reports.xml',
        'report/sale_order_templates.xml',
        'views/sale_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_report_generator/static/src/js/sale_report.js',
            'sale_report_generator/static/src/css/sale_report.css',
            'sale_report_generator/static/src/xml/sale_report_templates.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
