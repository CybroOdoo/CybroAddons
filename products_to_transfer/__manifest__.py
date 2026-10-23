# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Add Multiple Products to Inventory Transfer',
    'version': '20.0.1.0.0',
    'category': 'Warehouse',
    'summary': 'Easily add multiple products to a picking directly from the'
               ' product list view with this new feature',
    'description': "This module allows you to add multiple products to the "
                   "corresponding inventory transfer. You can see all products "
                   "in kanban, list and form view. You can also view the recent "
                   "transfer history of the selected product along with the "
                   "option to update the quantity, Inventory, Add Multiple "
                   "Products.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock'],
    'data': [
        'security/ir.access.csv',
        'views/stock_picking_views.xml',
        'views/product_product_views.xml',
        'wizard/transfer_products_details_views.xml',
        'wizard/wizard_add_to_draft_picking_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
