# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "Product Stock Details",
    'version': '14.0.1.0.0',
    'summary': """List And Print the Stock Details of Product""",
    'description': """This module has been developed for listing and printing product stock by location. 
                    Get an overview of Available, Forecasted, Incoming and Outgoing quantity of product from the
                    product form. The user can print these details in a PDF report.""",
    'author': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Inventory/Inventory',
    'depends': ['stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/product_view.xml',
        'reports/report.xml',
        'reports/template.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
