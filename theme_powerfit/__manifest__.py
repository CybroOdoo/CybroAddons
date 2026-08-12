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
{
    'name': 'Theme PowerFit',
    'version': '19.0.1.0.0',
    'category': 'Theme/Fitness',
    'summary': 'Premium Fitness & Gym Odoo Theme',
    'description': 'Premium Fitness & Gym Odoo Theme with modern animations and drag-and-drop snippets.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'hr', 'sale'],

    'data': [
        'security/ir.model.access.csv',
        'data/menu_data.xml',
        'views/hr_employee_views.xml',
        'views/product_template_views.xml',
        'views/layout.xml',
        'views/snippets/snippet_groups.xml',
        'views/snippets/s_powerfit_hero.xml',
        'views/snippets/s_powerfit_ticker.xml',
        'views/snippets/s_powerfit_about.xml',
        'views/snippets/s_powerfit_services.xml',
        'views/snippets/s_powerfit_trainers.xml',
        'views/snippets/s_powerfit_testimonials.xml',
        'views/snippets/s_powerfit_membership.xml',
        'views/snippets/s_powerfit_gallery.xml',
        'views/snippets/s_powerfit_lightbox.xml',
        'views/snippets/s_powerfit_transformation.xml',
        'views/snippets/s_powerfit_cta.xml',
        'views/snippets/s_powerfit_about_1.xml',
        'views/snippets/s_powerfit_about_2.xml',
        'views/snippets/s_powerfit_about_3.xml',
        'views/snippets/s_powerfit_about_4.xml',
        'views/snippets/s_powerfit_contact_1.xml',
        'views/snippets/s_powerfit_contact_2.xml',
        'views/snippets/s_powerfit_membership_1.xml',
        'views/snippets/s_powerfit_membership_2.xml',
        'views/snippets/s_powerfit_membership_3.xml',
        'views/snippets/s_powerfit_services_1.xml',
        'views/snippets/s_powerfit_services_2.xml',
        'views/snippets/s_powerfit_services_3.xml',
        'views/snippets/s_powerfit_trainers_1.xml',
        'views/snippets/s_powerfit_trainers_2.xml',
        'views/snippets/s_powerfit_trainers_3.xml',
        'views/home_templates.xml',
        'views/about_us_templates.xml',
        'views/services_templates.xml',
        'views/trainers_templates.xml',
        'views/membership_templates.xml',
        'views/contact_us_templates.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            'theme_powerfit/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            'theme_powerfit/static/src/scss/style.scss',
            'theme_powerfit/static/src/js/powerfit_core.js',
            'website/static/src/xml/website_form.xml',
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
}
