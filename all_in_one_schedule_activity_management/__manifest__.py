# -*- coding: utf-8 -*-
##############################################################################
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
    'name': 'All in one Schedule Activity Management',
    'version': '15.0.1.0.0',
    'category': 'Tools',
    'summary': 'The module allows the manage all scheduled activities.',
    'description': 'This app helps to manage all activities.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_setup', 'sale_management'],
    'data': [
        'data/due_date_notification.xml',
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/all_activity_view.xml',
        'views/activity_tag.xml',
        'views/my_activity.xml',
        'views/activity_dashbord.xml',
        'views/reporting_activity_view.xml',
        'views/activity_history_view.xml',
        'views/res_config_settings.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'all_in_one_schedule_activity_management/static/src/css/dashboard.css',
            'all_in_one_schedule_activity_management/static/src/css/style.scss',
            'all_in_one_schedule_activity_management/static/src/css/material-gauge.css',
            'all_in_one_schedule_activity_management/static/src/js/activity_dashboard.js',
        ],
        'web.assets_qweb': [
            'all_in_one_schedule_activity_management/static/src/xml/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
