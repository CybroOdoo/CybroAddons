# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#     Author:Anjhana A K(<https://www.cybrosys.com>)
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
    'version': '17.0.1.0.0',
    'category': 'Tools',
    'summary': """The module allows the manage all scheduled activities.""",
    'description': """The module is a robust tool for organizing and overseeing 
    all scheduled tasks and events, and Activity manager could manage scheduled 
    activities. """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_setup', 'mail', 'sale_management'],
    'data': [
        'security/all_in_one_schedule_activity_management_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/mail_activity_views.xml',
        'views/activity_tag_views.xml',
        'views/my_activity_views.xml',
        'views/activity_dashbord_views.xml',
        'views/reporting_activity_views.xml',
        'views/activity_history_views.xml',
        'views/res_config_setting_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'all_in_one_schedule_activity_management/static/src/js/activity_dashboard.js',
            'all_in_one_schedule_activity_management/static/src/xml/activity_dashboard_view.xml',
            'all_in_one_schedule_activity_management/static/src/css/dashboard.css',
            'all_in_one_schedule_activity_management/static/src/css/style.scss',
            'all_in_one_schedule_activity_management/static/src/css/material-gauge.css',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
