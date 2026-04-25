# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sreerag PM(<https://www.cybrosys.com>)
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
    'name': 'Vehicle Inspection Management in Fleet',
    'version': '18.0.1.0.0',
    'category': 'Industries',
    'summary': "Vehicle Inspection Management for managing the Vehicle"
               "Inspection and services.",
    'description': "Efficiently organize and oversee vehicle inspections and"
                   "services with  Vehicle Inspection Management system in"
                   "Odoo, ensuring optimal functionality and maintenance.",
    'depends': ['fleet'],
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'data': {
        'security/ir.model.access.csv',
        'security/vehicle_inspection_access.xml',
        'security/vehicle_inspection_management_security.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/vehicle_inspection_views.xml',
        'views/inspection_request_views.xml',
        'wizards/fleet_service_inspection_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/fleet_vehicle_log_services_views.xml',
        'views/vehicle_service_log_views.xml',
        'reports/vehicle_inspection_reports.xml',
        'reports/vehicle_inspection_report_templates.xml',
    },
    'license': 'AGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
