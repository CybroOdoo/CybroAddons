# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sidharth P (odoo@cybrosys.com)
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
    'name': 'Advanced Discuss Management',
    'version': '18.0.1.0.0',
    'category': 'Discuss',
    'summary': """Advanced kanban view for Discuss module.""",
    'description': """
        Advanced Discuss Management
        ===========================
        This module provides the Odoo 18 Discuss module with advanced views and features to boost productivity and improve the user interface.
        Key Features:
        -------------
        * **Kanban View for Chats:** Transforms the standard chat interface into an organized, easy-to-use Kanban view.
        * **Advanced Channels View:** Structured layout for better management of public and private channels.
        * **Quick Meeting Access:** Instantly start or join voice and video meetings directly from the reorganized sidebar.
        * **Mail & Chat Toggle:** Seamlessly switch between the dedicated Mail view and Chat views with single-click navigation.
        """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mail', 'base_setup','web'],
    'assets': {
        'web.assets_backend': [
            'advanced_discuss_management/static/src/css/discuss.css',
            'advanced_discuss_management/static/src/css/thread.css',
            'advanced_discuss_management/static/src/css/color.css',
            'advanced_discuss_management/static/src/js/discuss_sidebar.js',
            'advanced_discuss_management/static/src/js/discuss_sidebar_channel.js',
            'advanced_discuss_management/static/src/js/discuss_sidebar_categories.js',
            'advanced_discuss_management/static/src/xml/discuss_sidebar.xml',
            'advanced_discuss_management/static/src/xml/discuss_sidebar_startmeeting.xml',
            'advanced_discuss_management/static/src/xml/discuss_sidebar_category.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
