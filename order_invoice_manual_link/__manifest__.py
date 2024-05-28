# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
    'name': 'Sale Order Invoice Linker',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'This module designed to provide users with the ability to '
               'manually link invoices to specific sales orders',
    'description': "This module enhances user functionality within the Odoo "
                   "platform by enabling manual linkage of invoices to "
                   "specific sales orders. It empowers users to conveniently "
                   "associate invoices with their corresponding sales orders, "
                   "facilitating accurate record-keeping and streamlined "
                   "transaction management. Additionally, the module "
                   "incorporates validation checks to ensure data integrity, "
                   "such as verifying product consistency and detecting "
                   "partner mismatches between invoices and associated sales "
                   "orders. ",
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'account', 'stock_delivery'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'wizard/link_invoice_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
