# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': "CRM Dashboard",
    'description': """CRM Dashboard""",
    'summary': """CRM dashboard module brings a multipurpose graphical dashboard"""
               """ for CRM module and making the relationship management better and easier""",
    'category': 'Sales',
    'version': '15.0.1.0.2',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'crm', 'sale_management'],
    'data': [
        'views/dashboard_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'crm_dashboard/static/src/css/dashboard.css',
            'crm_dashboard/static/src/css/style.scss',
            'crm_dashboard/static/src/css/material-gauge.css',
            'crm_dashboard/static/src/js/dashboard_view.js',
            'crm_dashboard/static/src/js/custom.js',
            'crm_dashboard/static/src/js/lib/highcharts.js',
            'crm_dashboard/static/src/js/lib/Chart.bundle.js',
            'crm_dashboard/static/src/js/lib/funnel.js',
            'crm_dashboard/static/src/js/lib/d3.min.js',
            'crm_dashboard/static/src/js/lib/material-gauge.js',
            'crm_dashboard/static/src/js/lib/columnHeatmap.min.js',
            'crm_dashboard/static/src/js/lib/columnHeatmap.js',
        ],
        'web.assets_qweb': [
            'crm_dashboard/static/src/xml/dashboard_view.xml',
            # 'crm_dashboard/static/src/xml/sub_dashboard.xml',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
