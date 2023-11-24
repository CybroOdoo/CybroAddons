# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhil Ashok(<https://www.cybrosys.com>)
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
    'name': "POS Product Multi variant",
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """POS Multi-variant module is an advanced way for managing 
    product variants from the point of sale application""",
    'description': """POS Multi-variant module is an advanced way for managing
    product variants from the point of sale application. The module helps the 
    user to configure product variants straightfrom POS. User can set extra 
    price, also activate/inactivate the option for variants. As multi-variant 
    products are displayed with a label, it comes easy for the user to sort 
    which is multi-variant and which is not. User can confirm the variant type 
    to POS orders.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml'],
    'assets': {
        'point_of_sale.assets': [
            'pos_multi_variant/static/src/css/label.css',
            'pos_multi_variant/static/src/js/models.js',
            'pos_multi_variant/static/src/js/product_variant_orderline.js',
            'pos_multi_variant/static/src/js/ProductPopup.js',
            'pos_multi_variant/static/src/js/ProductScreen.js',
            'pos_multi_variant/static/src/xml/label.xml',
            'pos_multi_variant/static/src/xml/popup.xml'
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
