# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swathy K S (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Product Web Hover',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Hovering over a product in the order line will display '
               'a card containing the product details.',
    'description': 'When hovering over a product in the order line, '
                   'a product details card will be displayed, providing '
                   'additional information about the product',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'stock'],
    'assets': {
            'web.assets_backend': [
                'product_web_hover/static/src/xml/hoverTemplate.xml',
                'product_web_hover/static/src/js/listRenderer.js',
                'product_web_hover/static/src/js/popoverController.js',
                'product_web_hover/static/src/xml/listRenderer.xml'
            ],
        },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': True,
    'application': False,
}
