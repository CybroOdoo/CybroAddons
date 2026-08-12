# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Theme Medicare',
    'description': 'World-Class Healthcare Theme for Odoo',
    'category': 'Theme/Corporate',
    'summary': 'Medical, Healthcare, Hospital, Doctors, Appointments',
    'sequence': 110,
    'version': '18.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/medicare_demo_data.xml',
        'views/backend/medicare_department_views.xml',
        'views/backend/medicare_doctor_views.xml',
        'views/backend/medicare_appointment_views.xml',
        'views/backend/medicare_menus.xml',
        'data/website_menu_data.xml',
        'views/layout_templates.xml',
        'views/home_templates.xml',
        'views/about_templates.xml',
        'views/departments_templates.xml',
        'views/doctors_templates.xml',
        'views/patients_templates.xml',
        'views/research_templates.xml',
        'views/appointment_templates.xml',
        'views/contact_templates.xml',
        
        # Snippets
        'views/snippets/medicare_hero.xml',
        'views/snippets/medicare_stats.xml',
        'views/snippets/medicare_departments.xml',
        'views/snippets/medicare_doctors.xml',
        'views/snippets/medicare_appointment.xml',
        'views/snippets/medicare_emergency.xml',
        'views/snippets/medicare_mission.xml',
        'views/snippets/medicare_patient_services.xml',
        'views/snippets/medicare_research_areas.xml',
        'views/snippets/medicare_specialties_grid.xml',
        'views/snippets/medicare_doctor_block.xml',
        'views/snippets/medicare_testimonials.xml',
        'views/snippets/medicare_articles.xml',
        'views/snippets/snippet_groups.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_medicare/static/src/scss/style.scss',
            'theme_medicare/static/src/js/main.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
    'uninstall_hook': 'uninstall_hook',
}
