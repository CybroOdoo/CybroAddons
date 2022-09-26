#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "POS Kitchen Screen Dashboard",
    'version': "15.0.1.0.0",
    'category': "Tools",
    'summary': """
        Point of sale Kitchen Screen Dashboard
    """,
    'description': """
    Point of sale Kitchen Screen Dashboard
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'data': [
        'security/pos_kitchengroup.xml',
        'views/dashboard_menu_view.xml',
        'views/user_views.xml'
    ],
    'images': ['static/description/banner.png'],
    'depends': [
        'web',
        'point_of_sale',
        'pos_restaurant'
    ],
    "assets": {
        "web.assets_backend": [
            "pos_dashboard_ks/static/src/js/dashboard.js",
            "pos_dashboard_ks/static/src/css/custom.css",
        ],
        'web.assets_qweb': [
            "pos_dashboard_ks/static/src/xml/dashboard_template.xml",
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
