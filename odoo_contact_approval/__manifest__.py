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
    'name': "Odoo Contact Approval",
    'version': '15.0.1.0.0',
    'summary': """This module helps you manage contacts through the Approval manager's validation process""",
    "category": "Sales/Sales",
    'description': """The Odoo Contact Approval Module allows you to approve or cancel contacts through the Contacts
     Approval Manager. Only Approved contacts can be used in sales, purchasing, inventory, and invoice models.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'contacts', 'sale_management', 'purchase', 'stock', 'account'],
    'data': [
        'security/contact_approval_security.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}
