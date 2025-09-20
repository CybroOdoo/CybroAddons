# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Odoo Chatter Pin',
    'version': '18.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Pin and manage important messages or log notes in the chatter',
    'description': """This module allows users to pin important messages or log
                    notes within the chatter for quick reference. Users can e
                    asily view pinned messages, jump to them instantly, and 
                    unpin them when no longer needed. The pinned items are 
                    clearly marked with a pin icon for easy identification, 
                    enhancing message management and improving workflow 
                    efficiency.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'base', 'mail'],
    'data': [
    ],
    "assets": {
        "web.assets_backend":
            [
                'odoo_chatter_pin/static/src/css/style.css',
                'odoo_chatter_pin/static/src/xml/pinnedMessages.xml',
                'odoo_chatter_pin/static/src/js/pinMessage.js',
                'odoo_chatter_pin/static/src/js/chatter.js',
                'odoo_chatter_pin/static/src/js/message.js'
            ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
