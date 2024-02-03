# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Activity Management',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Dashboard for streamlined management of all activities.""",
    'description': """Simplify activity management with a comprehensive 
     dashboard, offering centralized control and oversight for seamless 
     organization-wide coordination and tracking.""",
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/activity_tag_views.xml',
        'views/activity_dashbord_views.xml',
        'views/mail_activity_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'activity_dashboard_mngmnt/static/src/css/dashboard.css',
            'activity_dashboard_mngmnt/static/src/css/style.scss',
            'activity_dashboard_mngmnt/static/src/css/material-gauge.css',
            'activity_dashboard_mngmnt/static/src/xml/activity_dashboard_template.xml',
            'activity_dashboard_mngmnt/static/src/js/activity_dashboard.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
