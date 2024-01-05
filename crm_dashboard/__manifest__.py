# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul Raj (odoo@cybrosys.com)
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
    'name': "CRM Dashboard",
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Get a visual report of CRM through a Dashboard in CRM """,
    'description': """CRM dashboard module brings a multipurpose graphical
     dashboard for CRM module and making the relationship management 
     better and easier""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['crm', 'sale_management'],
    'data': ['views/crm_team_views.xml',
             'views/res_users_views.xml',
             'views/utm_campaign_views.xml',
             ],
    'assets': {
        'web.assets_backend': [
            'crm_dashboard/static/src/css/dashboard.css',
            'crm_dashboard/static/src/css/style.scss',
            'crm_dashboard/static/src/css/material-gauge.css',
            'crm_dashboard/static/src/js/crm_dashboard.js',
            'crm_dashboard/static/src/js/lib/highcharts.js',
            'crm_dashboard/static/src/js/lib/Chart.bundle.js',
            'crm_dashboard/static/src/js/lib/funnel.js',
            'crm_dashboard/static/src/js/lib/d3.min.js',
            'crm_dashboard/static/src/js/lib/material-gauge.js',
            'crm_dashboard/static/src/js/lib/columnHeatmap.min.js',
            'crm_dashboard/static/src/js/lib/columnHeatmap.js',
            'crm_dashboard/static/src/xml/dashboard_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
