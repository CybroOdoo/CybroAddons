# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P(odoo@cybrosys.com)
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
    'name': 'Sales Commission',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': """To Create Sales Commission for Sales Person.""",
    'description': """Allows to create sales commission based on Product, 
    Partner, and Discount of Sale order to the sales person.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com/',
    'depends': ['sale_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sales_commission_report_views.xml',
        'views/commission_lines_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/sales_commission_views.xml',
        'views/sales_commission_menus.xml',
        'report/sales_commission_action.xml',
        'report/sales_commission_templates.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
