# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'Pos Button Visibility ',
    'depends': ['base', 'point_of_sale', 'pos_sale', 'pos_loyalty'],
    'version': '16.0.1.0.0',
    'category': 'Point Of Sale',
    'summary': """Pos button visibility is used to visible the buttons in the pos
     basis of users and sessions""",
    'description': """pos buttons can be restricted to the users in a specified sessions""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'data': {
        'security/ir.model.access.csv',
        'data/pos_button_visibility_data.xml',
        'views/res_users_views.xml',
    },
    'assets': {
        'point_of_sale.assets': [
            'pos_button_visibility/static/src/js/refundbutton.js',
            'pos_button_visibility/static/src/xml/refundbutton_templates.xml',
            'pos_button_visibility/static/src/xml/rewardbutton_templates.xml',
            'pos_button_visibility/static/src/xml/numpadwidget_templates.xml',
        ]
    },
}
