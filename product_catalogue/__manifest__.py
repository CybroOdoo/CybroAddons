# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': "Product Catalogue",
    'version': '12.0.1.0.0',
    'summary': """This module helps to print the catalogue of
                the single/multi products from the backend and single product
                from the E-commerce website
                including details like images and specifications""",
    'description': """This module helps to print the catalogue of
                the single/multi products from the backend and single product
                from the E-commerce website
                including details like images and specifications""",
    'category': 'Inventory',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'stock', 'website_sale'],
    'data': [
        'views/report_button_website.xml',
        'report/product_catalog_report.xml',
        'report/product_catalog_template.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
}
