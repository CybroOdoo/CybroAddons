# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    "name": "ChatGPT Odoo Connector",
    "version": "16.0.1.0.0",
    "category": "Productivity, Extra Tools ",
    "summary": "User can create content, Generate product image and Convert spoken language into written text using AI.",
    "description": """ This module simplifies content creation and editing by integrating ChatGPT.
    It also facilitates the generation of images for newly created products and 
    when modifying product names. Additionally, it includes a Speech-to-Text feature
    that allows users to convert spoken language into written text, making hands-free 
    interaction possible and further streamlining the content creation process.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mail', 'product', 'web_editor'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/product_template.xml',
        'views/product_product.xml',
    ],
    'assets': {
        'web_editor.assets_wysiwyg': [
            'chatgpt_odoo_connector/static/src/xml/web_editor_toolbar.xml',
            'chatgpt_odoo_connector/static/src/xml/alternative_chatgpt.xml',
        ],
        'web.assets_backend': [
            'chatgpt_odoo_connector/static/src/css/chatgpt_odoo.css',
            'chatgpt_odoo_connector/static/src/js/wysiwyg.js',
            'chatgpt_odoo_connector/static/src/js/open_chatgpt.js',
            'chatgpt_odoo_connector/static/src/js/recordAudio.js',
            'chatgpt_odoo_connector/static/src/js/custom_toolbar.js',
            'chatgpt_odoo_connector/static/src/js/alternative_chatgpt.js',
        ],
    },
    'external_dependencies': {'python': ['openai']},
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
