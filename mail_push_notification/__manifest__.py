# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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
    "name": "Push Notification From ChatBox",
    'version': '17.0.2.0.0',
    'category': 'Discuss,Extra Tools',
    'summary': """With Push Notification From ChatBox, users can respond 
     promptly to important messages, improving communication efficiency.""",
    'description': 'Push Notification From ChatBox is valuable for teams '
                   'looking to streamline communication and enhance '
                   'productivity within the Odoo platform.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "depends": ["web", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml"
    ],
    'assets': {
        'web.assets_backend': [
            "https://www.gstatic.com/firebasejs/8.4.3/firebase-app.js",
            "https://www.gstatic.com/firebasejs/8.4.3/firebase-messaging.js",
            "mail_push_notification/static/src/js/firebase.js",
        ],
    },
    "external_dependencies": {"python": ["firebase_admin"]},
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
