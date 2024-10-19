# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Purchase Product Configurator',
    'version': '18.0.1.0.0',
    'category': 'Purchases',
    'summary': """Purchase variant selection options for products.""",
    'description': """This module helps you to configure product variant
    selection in the purchase order lines.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['purchase_product_matrix'],
    'data': [
        'views/optional_product_template.xml',
        'views/purchase_order_views.xml',
        'views/product_template_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'purchase_product_configurator/static/src/js/purchase_product_field.js',
            'purchase_product_configurator/static/src/js/product_configurator_dialog/product_configurator_dialog.js',
            'purchase_product_configurator/static/src/js/product_configurator_dialog/product_configurator_dialog.xml',
            'purchase_product_configurator/static/src/js/product_list/product_list.js',
            'purchase_product_configurator/static/src/js/product_list/product_list.xml',
            'purchase_product_configurator/static/src/js/product/product.js',
            'purchase_product_configurator/static/src/js/product/product_template.xml',
            'purchase_product_configurator/static/src/js/product_template_attribute_line/product_template_attribute_line.js',
            'purchase_product_configurator/static/src/js/product_template_attribute_line/product_template_attribute_line.xml',
            'purchase_product_configurator/static/src/js/product/product.scss',
            'purchase_product_configurator/static/src/js/product_template_attribute_line/product_template_attribute_line.scss'
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
