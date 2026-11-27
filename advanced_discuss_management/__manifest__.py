# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Advanced Discuss Management',
    'version': '20.0.1.0.0',
    'category': 'Discuss',
    'summary': """Kanban board for Discuss chats, channels and meetings""",
    'description': """Advanced Discuss Management turns the Odoo 20 Discuss app
     into a board. The Chats, Channels and Meetings tabs of the sidebar show
     their conversations as Kanban cards with avatar, last message and unread
     counter, following the filters and search of the sidebar. Threads are
     listed right below their parent channel, a Meeting button starts a video
     meeting in one click, and the browser camera access is checked before
     the meeting starts.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mail'],
    'assets': {
        'web.assets_backend': [
            'advanced_discuss_management/static/src/discuss_kanban/discuss_kanban_board.js',
            'advanced_discuss_management/static/src/discuss_kanban/discuss_kanban_board.xml',
            'advanced_discuss_management/static/src/discuss_kanban/discuss_content_patch.js',
            'advanced_discuss_management/static/src/js/store_service_patch.js',
            'advanced_discuss_management/static/src/js/messaging_menu_patch.js',
            'advanced_discuss_management/static/src/xml/messaging_menu.xml',
            'advanced_discuss_management/static/src/scss/discuss_kanban.scss',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
