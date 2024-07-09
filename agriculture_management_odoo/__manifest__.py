# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav AR(<https://www.cybrosys.com>)
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
    'name': 'Agriculture Management',
    'version': '17.0.1.0.0',
    'category': 'Services',
    'summary': """ We Can Easily Manage the Agriculture to Our Own Need.""",
    'description': """ In the Agriculture Management App, We can manage the "
    "agriculture to our own need.We can also manage the rentals of vehicle and
     animals for agriculture purpose.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base','fleet', 'account'],
    'data': [
        'security/agriculture_management_groups.xml',
        'security/crop_request_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'report/crop_request_reports.xml',
        'report/pest_request_reports.xml',
        'report/crop_request_templates.xml',
        'report/pest_request_templates.xml',
        'report/crop_vehicle_templates.xml',
        'report/crop_animal_templates.xml',
        'report/crop_animal_reports.xml',
        'wizard/crop_report_views.xml',
        'wizard/pest_report_views.xml',
        'wizard/animal_register_payment_views.xml',
        'wizard/vehicle_register_payment_views.xml',
        'views/seed_detail_views.xml',
        'views/animal_detail_views.xml',
        'views/location_detail_views.xml',
        'views/vehicle_detail_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/farmer_detail_views.xml',
        'views/pest_request_views.xml',
        'views/pest_detail_views.xml',
        'views/damage_loss_views.xml',
        'views/crop_request_views.xml',
        'views/agriculture_tag_views.xml',
        'views/vehicle_rental_views.xml',
        'views/animal_rental_views.xml',
        'report/crop_vehicle_reports.xml',
        'views/agriculture_management_menus.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}

