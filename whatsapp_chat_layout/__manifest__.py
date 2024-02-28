# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (odoo@cybrosys.com)
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
    'name': 'Whatsapp Chat Layout in Odoo Discuss',
    'version': '17.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Redesigned the discuss module into whatsapp chat layout',
    'description': 'Odoo discuss with whatsapp view',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'mail', 'base_setup', 'web'],
    'data': [
        'views/res_config_settings.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'whatsapp_chat_layout/static/src/css/discuss.css',
            'whatsapp_chat_layout/static/src/css/thread.css',
            'whatsapp_chat_layout/static/src/css/color.css',
            'whatsapp_chat_layout/static/src/js/discuss_sidebar.js',
            'whatsapp_chat_layout/static/src/js/discuss_container.js',
            'whatsapp_chat_layout/static/src/xml/discuss_sidebar.xml',
            'whatsapp_chat_layout/static/src/xml/discuss_sidebar_category.xml',
            'whatsapp_chat_layout/static/src/xml/composer.xml'
            'whatsapp_chat_layout/static/src/xml/discuss_sidebar_categories_advanced.xml'
        ],
    },
    'images': [
        'static/description/banner.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
