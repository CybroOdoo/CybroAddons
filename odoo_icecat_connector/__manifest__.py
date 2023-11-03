# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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
    'name': 'Odoo Icecat Connector',
    'description': 'The Odoo Icecat Connector is a specialized module designed'
                   ' to integrate the Icecat database with an Odoo e-commerce'
                   ' website. Icecat is a leading global provider of product '
                   'content, offering a vast repository of rich product data '
                   'including descriptions, images, specifications, and more.',
    'summary': 'With the Odoo Icecat Connector, businesses can unleash the '
               'full potential of their Odoo e-commerce platform. By integrating'
               ' the Icecat database with Odoo, businesses can import '
               'accurate product details',
    'category': 'eCommerce',
    'version': '16.0.1.0.1',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'website_sale', 'stock'],
    'data': [
        'views/shop_templates.xml',
        'views/product_template_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'assets': {
        'web.assets_frontend': [
            'odoo_icecat_connector/static/src/js/icecat.js',
            'https://live.icecat.biz/js/live-current-2.js'
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
