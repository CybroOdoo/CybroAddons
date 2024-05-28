# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina P (odoo@cybrosys.com)
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
    'version': '17.0.1.0.0',
    'summary': 'Advanced kanban view for  Discuss module',
    'description': 'Odoo discuss module with advanced view and features',
    'category': 'Discuss',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'license': 'LGPL-3',
    'depends': ['mail', 'base_setup','web'],
    'assets': {
        'web.assets_backend': [
            'advanced_discuss_management/static/src/css/discuss.css',
            'advanced_discuss_management/static/src/css/thread.css',
            'advanced_discuss_management/static/src/css/color.css',
            'advanced_discuss_management/static/src/js/discuss_sidebar.js',
            'advanced_discuss_management/static/src/js/discuss_sidebar_categories.js',
            'advanced_discuss_management/static/src/xml/discuss_sidebar.xml',
            'advanced_discuss_management/static/src/xml/discuss_sidebar_startmeeting.xml',
            'advanced_discuss_management/static/src/xml/discuss_sidebar_channel.xml',
            'advanced_discuss_management/static/src/xml/discuss_sidebar_category.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
