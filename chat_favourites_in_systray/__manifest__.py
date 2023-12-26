# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abhin K(odoo@cybrosys.com)
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
    'name': "Chat Favourites In Systray",
    'version': '16.0.1.0.0',
    'category': 'Productivity',
    'summary': """Shortcut for viewing favourite chats from systray""",
    'description': "This module showcases favorite chat conversations "
                   "in the system tray, providing users with quick access "
                   "to favourite chats without navigating through the "
                   "full application interface.",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mail'],
    'data': [
        'views/res_users_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'chat_favourites_in_systray/static/src/js/messaging_menu.js',
            'chat_favourites_in_systray/static/src/js/channel_preview_view.js',
            'chat_favourites_in_systray/static/src/js/notification_list.js',
            'chat_favourites_in_systray/static/src/xml/systray.xml',
            'chat_favourites_in_systray/static/src/css/systray.css',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
