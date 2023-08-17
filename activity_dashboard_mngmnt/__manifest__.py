# -*- coding: utf-8 -*-
###################################################################################
#    Activity Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Activity Management',
    'version': '16.0.1.1.0',
    'category': 'Tools',
    'summary': 'Advance Activity Management and Dashboard View.',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'description': "Advance Activity Management and Dashboard View to track "
                   "activity of users.",
    'depends': ['base', 'mail'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/mail_activity_views.xml',
        'views/activity_tag_views.xml',
        'views/activity_dashbord.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'activity_dashboard_mngmnt/static/src/css/dashboard.css',
            'activity_dashboard_mngmnt/static/src/css/style.scss',
            'activity_dashboard_mngmnt/static/src/css/material-gauge.css',
            'activity_dashboard_mngmnt/static/src/xml/activity_dashboard_view.xml',
            'activity_dashboard_mngmnt/static/src/js/activity_dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'AGPL-3',
}
