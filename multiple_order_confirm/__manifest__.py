# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Jumana Jabin MP(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Multiple Sale/Purchase Order Confirm And Cancel',
    'version': '16.0.1.0.0',
    'category': 'Sales , Purchase',
    'summary': 'Manage Sales and Purchase Orders Effortlessly With Bulk '
               'Confirmation and Cancellation',
    'description': """Manage Sales and Purchase Orders Effortlessly Through 
    Bulk Confirmation and Cancellation.The "Multiple Sale/Purchase Order 
    Confirm And Cancel" module helps speed up the processing of your sales
    and purchase orders. This useful tool gives you the power to quickly
    confirm or reject several sale and purchase orders from the user-friendly
    Tree View interface.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'purchase'],
    'data': ['views/sale_order_views.xml',
             'views/purchase_order_views.xml'],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
