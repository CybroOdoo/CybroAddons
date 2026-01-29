# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'POS Chat Box',
    'category': 'Point Of Sale',
    'version': '15.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'summary': """POS Chat Box for Odoo16 community and enterprise edition""",
    'description': 'Using the POS screen, this module facilitates user '
                   'communication.',
    'images': ['static/description/banner.png'],
    'depends': [
        'base',
        'point_of_sale',
    ],
    'assets': {
        'web.assets_backend': [
            '/pos_chatter/static/src/js/pos_systray_icon.js',
            '/pos_chatter/static/src/js/pos_msg_view.js',
            '/pos_chatter/static/src/js/pos_chat_view.js',
        ],
        'web.assets_qweb': [
            '/pos_chatter/static/src/xml/pos_systray_icon.xml',
        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
