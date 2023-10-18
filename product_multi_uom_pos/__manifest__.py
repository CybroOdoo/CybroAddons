# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arwa V V (Contact : odoo@cybrosys.com)
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
    'name': "POS Product Multiple UOM",
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """A module to manage multiple UoM in POS""",
    'description': """This app allows you to change UoM of product in POS.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'point_of_sale'],
    'data':
        [
            'security/ir.model.access.csv',
            'views/res_config_settings_views.xml',
            'views/product_template_views.xml',
            'views/pos_order_views.xml',
        ],
    'assets': {
        'point_of_sale.assets': [
            'product_multi_uom_pos/static/src/js/Orderline.js',
            'product_multi_uom_pos/static/src/xml/Orderline.xml',
            'product_multi_uom_pos/static/src/xml/OrderReceipt.xml',
            'product_multi_uom_pos/static/src/js/load_pos_multi_uom.js',
            'product_multi_uom_pos/static/src/js/models.js',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
