# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    'name': 'Dental Clinic Management',
    'version': '18.0.1.0.0',
    'category': 'Services',
    'summary': """Dental Clinic Management is to manage the entire dental clinic.""",
    'description': """Dental Clinic Management software, dental clinics can 
    enhance efficiency, improve patient care, optimize resource utilization, 
    and maintain smooth operations.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['hr', 'website', 'mail', 'sale_management', 'purchase','stock'],
    'assets': {
        'web.assets_frontend': [
            "/dental_clinical_management/static/src/js/dental_clinic.js"
        ]
    },
    'data': [
        'security/dental_clinical_management_groups.xml',
        'security/dental_clinical_management_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/dental_department_data.xml',
        'data/dental_specialist_data.xml',
        'data/treatment_category_data.xml',
        'data/dental_treatment_data.xml',
        'data/insurance_company_data.xml',
        'data/medicine_frequency_data.xml',
        'data/dental_time_shift_data.xml',
        'data/website_menu.xml',
        'views/dental_time_shift_views.xml',
        'views/dental_department_views.xml',
        'views/dental_doctor_views.xml',
        'views/dental_patients_views.xml',
        'views/dental_prescription_views.xml',
        'views/dental_medicine_views.xml',
        'views/dental_specialist_views.xml',
        'views/dental_treatment_views.xml',
        'views/insurance_company_views.xml',
        'views/medicine_frequency_views.xml',
        'views/medical_questions_views.xml',
        'views/treatment_category_views.xml',
        'views/dental_appointment_views.xml',
        'views/patient_portal_template.xml',
        'views/dental_clinic_template.xml',
        'report/dental_appointment_card.xml',
        'report/dental_prescription_templates.xml',
        'report/dental_prescription_report.xml',
        'wizard/xray_report_views.xml',
        'views/dental_clinical_management_menu.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
