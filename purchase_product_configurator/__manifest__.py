# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayisha Sumayya K, Vivek (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Purchase Product Configurator',
    'version': '16.0.1.0.0',
    'category': 'Purchases',
    'summary': """Helps to configure the product in purchase order line""",
    'description': """The module helps you to override purchase_order_line"""
                """to configurate product in RFQ """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'depends': ['purchase', 'sale', 'base', 'purchase_product_matrix'],
    'data': [
            'views/optional_product_template.xml',
            'views/purchase_order_views.xml',
            'views/product_template_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'purchase_product_configurator/static/src/js/basic_model.js',
            'purchase_product_configurator/static/src/js/product_configurator.js',
            'purchase_product_configurator/static/src/js/purchase_product_field.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False
}
