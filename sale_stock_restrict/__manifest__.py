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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    'name': 'Sale Stock Restrict',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': """Sale Stock Restrict, Out of Stock Restriction, Restrict Sale Order, Stock Validation, On Hand Quantity, Forecast Quantity, Odoo20 Sales, Odoo20 Inventory""",
    'description': """
     Restrict the confirmation of sale orders when products are out of stock.
     From the Sales settings, enable the restriction and choose whether stock
     is checked against the on hand or the forecast quantity. The chosen
     quantity is shown on each order line, and confirming an order that asks
     for more than is available raises a warning listing every short product.
     Only products that track inventory are checked, units of measure are
     converted before comparing, and website orders are not restricted.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_stock', 'website_sale'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
