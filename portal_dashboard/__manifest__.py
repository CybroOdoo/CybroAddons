# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Megha A P (odoo@cybrosys.com)
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
    'name': "Portal Dashboard",
    'version': '16.0.1.0.0',
    'summary': """Portal Dashboard to view the my account in dashboard view""",
    'description': 'View of my account in portal view is changed to dashboard '
                   'view for better user experience',
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'sale', 'project', 'crm', 'purchase', 'website'],
    'images': [
        '/static/description/banner.png',
    ],
    'data': [
        'views/res_config_settings_views.xml',
        'views/dashboard.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'portal_dashboard/static/src/js/portal_dashboard_graph.js',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js',
            '/portal_dashboard/static/src/scss/style.scss'
        ]
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': True,
    'application': False,
}
