# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
    'name': 'Event Management and Catering',
    'version': '18.0.1.0.1',
    "category": "Industries",
    'summary': """Comprehensive event management with integrated catering 
     service.""",
    'description': """This module combines event management and catering 
     services, allowing you to manage event types, service orders, and 
     invoicing efficiently—all from a single interface in Odoo.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['product', 'account'],
    'data': [
        'security/security_group.xml',
        'security/ir.model.access.csv',
        'security/security_rule.xml',
        'data/event_management_data.xml',
        'data/ir_sequence_data.xml',
        'reports/event_management_report_templates.xml',
        'reports/event_management_report.xml',
        'views/event_management_views.xml',
        'views/event_management_type_views.xml',
        'views/event_management_catering_views.xml',
        'wizard/event_management_report_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'event_management/static/src/css/dashboard.css',
            'event_management/static/src/js/action_manager.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
