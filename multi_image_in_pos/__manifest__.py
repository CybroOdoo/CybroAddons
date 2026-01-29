# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
    'name': 'Multiple Images in PoS',
    'version': '15.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Show multiple images of products in pos',
    'description': 'Multiple image in pos helps add user multiple images for'
                   'product and to view them in pos',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/multi_image_views.xml',
        'views/product_product_views.xml',
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'multi_image_in_pos/static/src/js/product_item.js',
            'multi_image_in_pos/static/src/js/multi_image_popup.js',
            'multi_image_in_pos/static/src/css/multi_image_popup_style.scss',
        ],
        'web.assets_qweb': [
            'multi_image_in_pos/static/src/xml/product_item_templates.xml',
            'multi_image_in_pos/static/src/xml/image_popup_templates.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
