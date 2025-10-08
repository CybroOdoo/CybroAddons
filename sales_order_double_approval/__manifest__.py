# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Sales Order Double Approval',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': """ "Sales Order Double Approval" is a process requiring two 
                    separate approvals for a sales order to ensure accuracy, 
                    compliance, and reduce the risk of errors and fraud. """,
    'description': """ "Sales Order Double Approval" refers to a process where 
                        a sales order must be reviewed and approved by two 
                        separate individuals or departments before it is 
                        finalized. This is implemented to ensure accuracy, 
                        compliance, and reduce the risk of errors and fraud 
                        in sales transactions. """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com/',
    'depends': ['base', 'sale_management'],
    'data': [
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml'
    ],
    'images': [
        'static/description/banner.png',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
