# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Mail Message Access',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Implement the restriction on chatter messages for the users',
    'description': 'In Odoo chatter, you can restrict chatter messages for '
                   'users by implementing access rights. By setting specific '
                   'access permissions, you can control who can send messages '
                   'and what actions they you to ensure a secure and '
                   'controlled messaging environment, maintaining data '
                   'integrity and promoting efficient collaboration within '
                   'the platform.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_setup', 'mail'],
    'data': [
        'security/mail_message_access_groups.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mail_message_access/static/src/models/chatter.js',
            'mail_message_access/static/src/components/chatter_topbar/chatter_topbar.xml'
        ]
    },
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
