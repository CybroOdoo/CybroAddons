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
    'summary': """Product Approval Management""",
    'description': """
        Using this module a user can create product which will be in 
             draft state and only a product manager can confirm the product.
             Also only the confirmed products can be selected from 
             sale order line
        """,
    'category': "Sales/Sales",
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['sale_management'],
    'data': [
        'security/approve_security.xml',
        'security/ir.model.access.csv',
        'views/product_approval_views.xml'
    ],
    'images': ['static/description/banner.png'],
    'version': '14.0.2.2.0',
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
