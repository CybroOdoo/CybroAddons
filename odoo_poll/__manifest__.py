# -*- coding: utf-8 -*-
################################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#   Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#   This program is free software: you can modify
#   it under the terms of the GNU Affero General Public License (AGPL) as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'Odoo Poll',
    'version': '18.0.1.0.0',
    'category': 'Productivity/Discuss',
    'summary': 'Create and vote on polls in Discuss channels',
    'description': """Create polls with multiple options""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail','web'],
    'data': [
             'security/odoo_poll_security.xml',
             'security/ir.model.access.csv',
             'views/poll_views.xml',
            ],
    "assets": {
        "web.assets_backend": [
            "odoo_poll/static/src/scss/poll.scss",
            "odoo_poll/static/src/js/composer_patch.js",
            "odoo_poll/static/src/js/poll_dialog.js",
            "odoo_poll/static/src/js/poll_message.js",
            "odoo_poll/static/src/js/poll_service.js",
            "odoo_poll/static/src/js/mail_message_patch.js",
            "odoo_poll/static/src/xml/poll_composer.xml",
            "odoo_poll/static/src/xml/poll_dialog.xml",
            "odoo_poll/static/src/xml/poll_message.xml",
            "odoo_poll/static/src/xml/message_patch.xml",
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
