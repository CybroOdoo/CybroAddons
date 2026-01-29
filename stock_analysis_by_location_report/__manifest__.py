# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
{
    'name': "Stock Analysis By Location Report",
    'version': '15.0.1.0.0',
    'category': 'Warehouse',
    'summary': """Analyse the product or product variant stock based on
    locations.""",
    'description': """This module helps to analyse the stock informations in
    each location. Also enables to print the details as a PDF or Excel report.""",
    'author': " Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_location_product_views.xml',
        'views/stock_location_product_variant_views.xml',
        'views/product_template_views.xml',
        'report/stock_location_report.xml',
        'report/stock_location_report_templates.xml',
        'wizard/stock_location_report_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stock_analysis_by_location_report/static/src/js/stock_report.js'
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
