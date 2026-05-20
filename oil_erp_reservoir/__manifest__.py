# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Oil & Gas Reservoir',
    'version': '19.0.2.0.0',
    'category': 'Oil ERP/Reservoir Management',
    'summary': 'Track underground reservoirs, reserves, geology data',
    'description': """
Reservoir Management module for the Oil & Gas ERP system.
Provides tracking for underground reservoirs, geological conditions, fluid types,
estimated reserves, and current status.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'oil_erp_base',
        'oil_erp_project',
    ],
    'data': [
        'security/oil_reservoir_security.xml',
        'security/ir.model.access.csv',
        'data/project_project_data.xml',
        'views/oil_reservoir_views.xml',
        'views/project_project_views.xml',
        'views/project_project_stage_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': '_auto_enable_project_stages',
}
