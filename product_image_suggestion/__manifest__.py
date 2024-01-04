# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Vishnu kp(<https://www.cybrosys.com>)
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
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Suggest product images from google search',
    'description': "Product images can be searched from the product form using"
                   " bing image downloader and it can be set as the product "
                   "display image.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'external_dependencies': {'python': ['Pillow', 'python-resize-image']},
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
