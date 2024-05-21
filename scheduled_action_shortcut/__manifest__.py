# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
    'name': 'Scheduled Action Shortcut',
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Scheduled Action Shortcut to run through systray""",
    'description': """Scheduled Action Shortcut helps you to run the scheduled 
     actions through systray""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base'],
    'data': [
        'views/ir_cron_views.xml'
    ],
    'assets':
        {
            'web.assets_backend': [
                'scheduled_action_shortcut/static/src/js/systray_icon_scheduled_action.js',
                'scheduled_action_shortcut/static/src/js/scheduled_actions.js',
                'scheduled_action_shortcut/static/src/css/style.css'
            ],
            'web.assets_qweb': [
                'scheduled_action_shortcut/static/src/xml/systray_icon.xml',
            ]
        },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
