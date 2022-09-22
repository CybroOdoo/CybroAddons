# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    'name': "Chat Favourites in Systray",
    'version': '15.0.1.0.0',
    'summary': """Shortcut for Viewing Favourite Chats From Systray""",
    'description': """This module display favourite chats from a shortcut in systray""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'category': 'Tools',
    'depends': ['base', 'mail'],
    'data': [
        'views/mail_message_views.xml'],
    'assets': {
        'web.assets_backend': [
            'chat_favourites_in_systray/static/src/js/messaging_menu.js',
            'chat_favourites_in_systray/static/src/js/thread_preview.js',
            'chat_favourites_in_systray/static/src/js/notification_list.js',
            'chat_favourites_in_systray/static/src/js/thread.js',
        ],
        'web.assets_qweb': [
            'chat_favourites_in_systray/static/src/xml/systray.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
