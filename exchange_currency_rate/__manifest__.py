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
    'name': "Manual Currency Exchange Rate",
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': """By using this module ,we can change the currency rate manually
     in sale ,purchase and invoice. """,
    'description': """By using this module, we can manually adjust the currency
     rate for key aspects of our business operations, including sales,
     purchases, and invoicing. This feature gives us the power to have precise
     control over currency conversions and adapt quickly to fluctuating 
     exchange rates.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'purchase', 'sale_management', 'account'],
    'data': [
        'views/account_move_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
