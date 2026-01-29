# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreejith sasidharan(<https://www.cybrosys.com>)
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
    'version': '15.0.1.0.2',
    'summary': """Product with multi-variants""",
    'description': """Configure products having variants in POS""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'category': 'Point of Sale',
    'depends': ['base',
                'point_of_sale',
                ],
    'data': ['views/pos_variants.xml',
             'security/ir.model.access.csv',
             ],

    'assets': {
        'point_of_sale.assets': [
            'pos_multi_variant/static/src/css/label.css',
            'pos_multi_variant/static/src/js/models.js',
            'pos_multi_variant/static/src/js/ProductPopup.js',
            'pos_multi_variant/static/src/js/ProductScreen.js'
        ],
        'web.assets_qweb': [
            'pos_multi_variant/static/src/xml/label.xml',
            'pos_multi_variant/static/src/xml/popup.xml'
        ],
    },

    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,



    'auto_install': False,
}
