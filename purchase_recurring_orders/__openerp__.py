# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jesni Banu(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Purchase Recurring orders',
    'version': '9.0.1.0.0',
    'summary': 'Purchase Recurring orders',
    'description': 'This module allows you to create recurring orders for purchases.',
    'category': 'Purchases',
    'author': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com/odoo/industries/purchasing-management-software/',
    'company': 'Cybrosys Techno Solutions',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/recurring_orders_data.xml',
        'wizard/renew_wizard_view.xml',
        'views/recurring_orders_view.xml',
        'views/purchase_order_view.xml',
        'views/res_partner_view.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
