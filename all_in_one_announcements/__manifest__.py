# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'All In One Announcements',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """The module helps to analyse the work progress.""",
    'description': """The module gives a complete analysis of the work
    progress and also helps to send the work progress through email to the 
    manager.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'project', 'purchase', 'sale_management', 'crm', 'mail',
                'contacts'],
    'data': ['security/all_in_one_announcements_group.xml',
             'data/ir_cron_data.xml',
             'views/res_config_settings_views.xml',
             'views/email_templates.xml',
             ],
    'assets': {
        'web.assets_backend': [
            'all_in_one_announcements/static/src/js/systray.js',
            'all_in_one_announcements/static/src/css/specs.css',
            'all_in_one_announcements/static/src/xml/announcement_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
