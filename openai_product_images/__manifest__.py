# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'Generate Product Images Using OpenAI',
    'version': '17.0.2.0.0',
    'category': 'Extra Tools',
    'summary': 'This module helps to generate images for products using OpenAI.',
    'description': 'Odoo module for generating product images using '
                   'OpenAI,AI Image,openai_image,chatgpt,odoo chatgpt connector,'
                   'odoo chatgpt,openai odoo',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'product', 'openai_odoo_base'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/openai_image_suggestion_views.xml',
        'wizard/image_suggestion_views.xml',
    ],
    'external_dependencies': {
       'python': ['openai'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
