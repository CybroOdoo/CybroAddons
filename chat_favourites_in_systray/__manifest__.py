# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
{
    'name': "Chat Favourites In Systray",
    'version': '19.0.1.0.0',
    'category': 'Productivity/Discuss',
    'summary': """Quick access to favourite chats and channels from systray""",
    'description': """This module enhances the Odoo messaging experience by introducing a convenient way to add and 
     access favourite chats and channels directly from the system tray (systray). Users can mark important 
     conversations and channels as favourites, allowing them to quickly navigate to frequently used discussions without 
     browsing through the full messaging interface.              
     Key Features:
        - Add chats and channels to favourites
        - Access favourite conversations instantly from the systray
        - Improve productivity with reduced navigation time
        - Seamless integration with Odoo's existing messaging system
     This feature is especially useful for users who regularly interact with specific contacts or 
     channels and need faster access within their daily workflow.""",
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
            'chat_favourites_in_systray/static/src/core/public_web/notification_item.js',
            'chat_favourites_in_systray/static/src/core/public_web/messaging_menu.js',
            'chat_favourites_in_systray/static/src/core/public_web/notification_item.xml',
            'chat_favourites_in_systray/static/src/core/public_web/messaging_menu.xml',
            'chat_favourites_in_systray/static/src/core/public_web/messaging_menu.css',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
