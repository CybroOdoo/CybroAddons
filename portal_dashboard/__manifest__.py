# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
    'version': '15.0.1.0.0',
    'category': 'Website',
    'summary': "Portal Dashboard to view the My Account Details in Dashboard "
               "view",
    'description': "Portal Dashboard enhances your website's user experience "
                   "by providing a feature-rich dashboard for My Account "
                   "details. With a sleek and intuitive design, users can "
                   "easily navigate and access key information at a glance.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management', 'project', 'crm', 'purchase', 'website'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/portal_dashboard_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'portal_dashboard/static/src/js/portal_dashboard_graph.js',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js',
            '/portal_dashboard/static/src/scss/portal_dashboard_style.scss'
        ]
    },
    'images': ['static/description/banner.png', ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
