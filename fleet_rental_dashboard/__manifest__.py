# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
    'name': 'Fleet Rental Dashboard',
    'version': '16.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Dashboard for fleet rental management',
    'description': 'This dashboard module enhances the fleet rental management '
                   'system by offering a centralized view of crucial metrics'
                   ' and analytics.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['fleet_rental', 'base'],
    'data': ['views/fleet_rental_dashboard_views.xml',
             ],
    'assets': {
        'web.assets_backend': [
            'fleet_rental_dashboard/static/src/js/dashboard.js',
            'fleet_rental_dashboard/static/src/css/dashboard.css',
            'fleet_rental_dashboard/static/src/css/style.scss',
            'fleet_rental_dashboard/static/src/js/lib/Chart.bundle.js',
            'fleet_rental_dashboard/static/src/xml/dashboard_templates.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
