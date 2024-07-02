# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
{
    "name": "CRM Kit",
    "version": '17.0.1.0.1',
    "category": 'Sales',
    'summary': """Complete CRM Kit for odoo 17""",
    'description': """Complete CRM Kit for odoo 17, CRM, CRM dashboard, 
     crm commission, commission plan, crm features""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "depends": ['sale_management', 'crm', 'crm_dashboard'],
    "data": [
        'security/ir.model.access.csv',
        'views/crm_commission_views.xml',
        'views/crm_team_views.xml',
        'views/res_users_views.xml',
        'wizard/commission_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'crm_kit/static/src/js/action_manager.js',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
