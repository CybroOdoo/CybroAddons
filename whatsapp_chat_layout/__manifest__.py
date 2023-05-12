# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
    'version': '16.0.1.0.0',
    'summary': 'Redesigned the discuss module into whatsapp chat layout',
    'description': 'Odoo discuss with whatsapp view',
    'category': 'Discuss',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'base_setup'],
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
            'whatsapp_chat_layout/static/src/xml/discuss_sidebar_mailbox.xml',
            'whatsapp_chat_layout/static/src/xml/composer.xml'
        ],
    },
    'images': [
        'static/description/banner.png'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
