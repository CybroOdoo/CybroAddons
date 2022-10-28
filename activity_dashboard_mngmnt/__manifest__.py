# -*- coding: utf-8 -*-
###################################################################################
#    Activity Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Megha K (<https://www.cybrosys.com>)
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
    'version': '15.0.1.0.0',
    'category': 'Tools',
    'summary': 'Advance Activity Management and Dashboard View',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'description': "Advance Activity Management and Dashboard View",
    'depends': ['base', 'mail'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/my_activity.xml',
        'views/activity_tag.xml',
        'views/activity_dashbord.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'activity_dashboard_mngmnt/static/src/css/dashboard.css',
            'activity_dashboard_mngmnt/static/src/css/style.scss',
            'activity_dashboard_mngmnt/static/src/css/material-gauge.css',
            'activity_dashboard_mngmnt/static/src/js/activity_dashboard.js',
        ],
        'web.assets_qweb': [
            'activity_dashboard_mngmnt/static/src/xml/activity_dashboard_view.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
