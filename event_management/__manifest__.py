# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
    'version': '14.0.1.0.0',
    "category": "Industries",
    'summary': """Event management is a core module which can manage any
    type of events in odoo 14.""",
    'description': """Event management module use to manage different service 
     modules to extend the scope of this module. The new service will be 
     automatically get attached to this core Event management module. It is 
     different from Odoo's event module. Here you can manage different types of
      events and allocate services to different users.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['account'],
    'data': ['security/event_management_groups.xml',
             'security/event_management_security.xml',
             'security/ir.model.access.csv',
             'data/event_management_data.xml',
             'views/assets.xml',
             'views/event_management_views.xml',
             'views/event_management_type_views.xml',
             'views/dashboard_action.xml',
             'report/event_management_templates.xml',
             'report/event_management_reports.xml',
             'wizard/event_management_report_views.xml',
             ],
    'assets': {
        'web.assets_backend': [
            "event_management/static/src/css/event_dashboard.css",
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
