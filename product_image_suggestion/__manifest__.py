# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Prasudhi A<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Product Image Suggestion',
    "version": "19.0.1.0.0",
    'category': 'Productivity',
    'summary': """Search product images via Bing Image Downloader in the product
     form and set as display image.""",
    'description': """This module helps by allowing you to search for product 
     images directly from the product form using the Bing Image Downloader tool.
     Once found, these images can be set as the display image for the 
     product.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'external_dependencies': {
            'python': ['Pillow', 'python-resize-image']
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
