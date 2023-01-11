# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Agriculture Management In Odoo',
    'version': '15.0.2.0.0',
    'summary': 'Agriculture Management In Odoo',
    'description': """Agriculture Management In Odoo""",
    'category': 'Productivity',
    'website': 'https://www.cybrosys.com',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'fleet',
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'data/data_sequence.xml',
        'report/crop_report.xml',
        'report/pest_report.xml',
        'report/crop_report_template.xml',
        'report/pest_report_template.xml',
        'report/crop_vehicle_report.xml',
        'report/crop_animal_report.xml',
        'wizard/crop_report_wiz.xml',
        'wizard/pest_report_wiz.xml',
        'views/menu_action.xml',
        'views/menu_items.xml',
        'views/seed_details_view.xml',
        'views/animal_details_views.xml',
        'views/location_details_view.xml',
        'views/vehicle_details_view.xml',
        'views/fleet_inherit_view.xml',
        'views/farmer_details_view.xml',
        'views/pest_request.xml',
        'views/pest_details.xml',
        'views/damage_loss.xml',
        'views/crop_request.xml',
        'views/tag_details.xml',
        'views/vehicle_rental_views.xml',
        'views/animal_rental_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
