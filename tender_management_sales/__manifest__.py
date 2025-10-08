# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Nikhil M (odoo@cybrosys.com)
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
    'name': 'Tender Management Sales',
    'version': "16.0.1.0.0",
    'summary': 'Tender Management in Sales and Option to Compare Orders',
    'description': """Tender Management in Sales and Option to Compare Orders""",
    'category': 'Sale',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/sale_tender_data.xml',
        'views/tender_sales_views.xml',
        'views/sale_order_views.xml',
        'wizard/tender_sales_create_alternative.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tender_management_sales/static/src/widgets/sale_order_alternatives_widget.js',
            'tender_management_sales/static/src/widgets/sale_order_alternatives_widget.scss',
            'tender_management_sales/static/src/widgets/sale_order_alternatives_widget.xml',
            'tender_management_sales/static/src/views/list/sale_order_line_compare_list_renderer.js',
            'tender_management_sales/static/src/views/list/sale_order_line_compare_list_view.js',
        ],
    },
    'license': 'AGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
