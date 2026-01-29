# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP(odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Vehicle Inspection Management In Fleet',
    'version': '15.0.1.0.0',
    'category': 'Industries',
    'summary': 'Vehicle Inspection Management for manage the Vehicles',
    'description': "Vehicle Inspection Management used to manage the "
                   "Vehicle's Inspection and Services, User can add real time "
                   "images for service",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'fleet'],
    'data': {
        'security/fleet_vehicle_inspection_management.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_template_data.xml',
        'views/vehicle_inspection_views.xml',
        'views/inspection_request_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/fleet_vehicle_log_services_views.xml',
        'views/vehicle_service_log_views.xml',
        'report/vehicle_service_log_reports.xml',
        'report/vehicle_service_log_templates.xml',
        'wizard/fleet_service_inspection_views.xml',
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
