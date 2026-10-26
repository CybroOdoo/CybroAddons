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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': "Sales And Products Performance Report",
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Performance Report Summary of Sales and Products',
    'description': "Overview of the sales and products performance "
                   "by sales team and sales person",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    # sale_management activates the Sales app root menu (sale.sale_menu_root,
    # inactive in the bare ``sale`` module) that holds the report menus.
    'depends': ['sale_management', 'sale_stock'],
    'data': [
        'security/ir.access.csv',
        'wizard/product_performance_views.xml',
        'wizard/sales_performance_views.xml',
        'views/product_performance_line_views.xml',
        'views/sales_performance_line_views.xml',
        'views/sale_order_menu.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
