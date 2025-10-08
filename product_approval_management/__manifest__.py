# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
    'name': "Product Approval",
    'version': '16.0.1.0.0',
    'category': "Extra tools",
    'summary': 'Product approval allow you to control the product creation',
    'description': "Using this module a user can create product which"
    "will be in draft state and only a product manager can"
    "confirm the product.Also only the confirmed products"
    "can be selected from sale order line",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management'],
    'data': ['security/product_approval_management_groups.xml',
             'security/ir.model.access.csv',
             'views/product_template_views.xml',
             'views/sale_order_views.xml'],
    'images': ['static/description/banner.jpg'],
    'post_init_hook': '_default_product_confirm',
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
