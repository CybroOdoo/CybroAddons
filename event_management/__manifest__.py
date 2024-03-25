# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Subina P (odoo@cybrosys.com)
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
    'name': 'Event Management',
    'version': '17.0.1.0.0',
    "category": "Industries",
    'summary': """Event Management module for manage events.""",
    'description': """Event management module is a core module for managing
     different types of events""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['product', 'account'],
    'data': ['security/event_management_security.xml',
             'security/ir.model.access.csv',
             'data/event_management_type_data.xml',
             'reports/pdf_report_templates.xml',
             'reports/event_management_reports.xml',
             'views/event_management_views.xml',
             'views/event_management_type_views.xml',
             'wizards/event_management_report_views.xml',
             ],
    'assets': {
        'web.assets_backend': [
            "event_management/static/src/css/event_dashboard.css",
            "event_management/static/src/js/action_manager.js"
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
