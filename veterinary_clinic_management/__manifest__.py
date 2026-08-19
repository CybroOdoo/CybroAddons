# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Veterinary Clinic Management',
    'version': '18.0.1.0.0',
    'category': 'Industries',
    'summary': """Manage appointments, invoicing, and patient records for veterinary services.""",
    'description': """ This module helps in scheduling appointments, managing invoices, and storing patient records for
     animal patients. It includes various functionalities to manage different aspects of veterinary services such as 
     surgery, grooming, training, and more.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'product', 'contacts','account','stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/product_demo.xml',
        'views/res_patient_views.xml',
        'views/account_move_views.xml',
        'views/product_product_views.xml',
        'views/animal_types_views.xml',
        'views/breed_types_views.xml',
        'views/disease_types_views.xml',
        'views/surgery_types_views.xml',
        'views/animal_vaccine_views.xml',
        'views/case_appointments_views.xml',
        'views/animal_grooming_views.xml',
        'views/animal_training_views.xml',
        'views/training_package_views.xml',
        'views/training_inclusion_views.xml',
        'views/training_exclusion_views.xml',
        'views/surgery_appointment_views.xml',
        'views/veterinary_employees_views.xml',
        'views/prescription_orders_views.xml',
        'views/medical_report_views.xml',
        'views/res_maintenance_views.xml',
        'views/product_template_views.xml',
        'views/room_details_views.xml',
        'views/veterinary_client_action.xml',

        'report/prescription_order_views.xml',
        'report/prescription_order_templates.xml',
        'report/veterinary_clinic_management_reports.xml',
        'report/veterinary_clinic_management_templates.xml',
        'report/res_patients_views.xml',
        'report/res_patients_templates.xml',
        'report/case_appointments_views.xml',
        'report/case_appointments_templates.xml',

        'wizard/veterinary_appointment_views.xml',
        'wizard/veterinary_clinic_management_views.xml',
    ],
    'assets': {
            'web.assets_backend': [
                'veterinary_clinic_management/static/src/js/veterinary_dashboard.js',
                'veterinary_clinic_management/static/src/xml/veterinary_dashboard_views.xml',
                'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js'
            ],
        },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
