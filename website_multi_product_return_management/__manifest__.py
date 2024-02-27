# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R (odoo@cybrosys.com)
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
    'name': 'Multi Product Return From Website',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Sale order multi product return management from website',
    'description': "Streamline your website with advanced Multi-product Return "
                   "Order Management. Easily manage returns, RMA, and order "
                   "return processes directly from your website.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale', 'stock', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/website_thankyou_template.xml',
        'views/sale_order_portal_templates.xml',
        'views/sale_return_views.xml',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'views/stock_picking_views.xml',
        'report/sale_return_templates.xml',
        'report/sale_return_reports.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_multi_product_return_management/static/src/js/sale_return.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
