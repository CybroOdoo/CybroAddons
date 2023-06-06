# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vivek @ cybrosys,(odoo@cybrosys.com)
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
    'name': 'Website Decimal Quantity',
    'version': '16.0.1.0.0',
    'category': 'Website/Website',
    'summary': 'The app allows to select quantity in decimal for products in Website/Shop',
    'description': """
    The app allows to select quantity in decimal for products in Website/Shop
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.png'],
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale'],
    'data': ['views/website_sale_templates.xml'],
    'assets': {
        'web.assets_frontend': [
            '/website_decimal_quantity/static/src/js/variant_mixin.js',
            '/website_decimal_quantity/static/src/js/website_sale.js',
            '/website_decimal_quantity/static/src/js/website_sale_utils.js',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
