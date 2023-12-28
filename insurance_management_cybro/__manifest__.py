# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen @cybrosys (odoo@cybrosys.com)
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
    'name': 'Insurance Management',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': """Insurance Management & Operations of the customers and manage
     the insurance claims and the salary of agents with or without the 
     commission.""",
    'description': """Insurance Management and claims based on policies allows
     the user to create insurance policies """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_type_data.xml',
        'data/insurance_details_data.xml',
        'data/claim_details_data.xml',
        'views/claim_details_views.xml',
        'views/employee_details_views.xml',
        'views/insurance_details_views.xml',
        'views/policy_details_views.xml',
        'views/insurance_management_menus.xml',
        'views/policy_type_views.xml',
        'views/payment_type_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'account/static/src/components/**/*',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
