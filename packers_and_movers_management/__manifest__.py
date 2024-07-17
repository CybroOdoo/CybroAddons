# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
    'name': 'Packers & Movers Management',
    'version': '17.0.1.0.0',
    'category': 'Industries,Website',
    'summary': """Users can reserve trucks online with the help of the 
    Packers & Movers Management module.""",
    'description': """The Packers & Movers Management module helps Users to 
    book the trucks through online""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'fleet', 'mail', 'account'],
    'data': [
        'security/packers_and_movers_security.xml',
        'security/ir.model.access.csv',
        'data/truck_booking_sequence.xml',
        'data/website_form_data.xml',
        'data/goods_type_data.xml',
        'data/truck_type_data.xml',
        'data/fleet_truck_data.xml',
        'report/booking_form_report_templates.xml',
        'report/booking_report_templates.xml',
        'report/booking_report_views.xml',
        'views/website_page_booking_templates.xml',
        'views/goods_type_views.xml',
        'views/truck_booking_views.xml',
        'views/website_page_goods_templates.xml',
        'views/website_page_truck_templates.xml',
        'views/fleet_vehicle_model_views.xml',
        'views/res_config_settings_views.xml',
        'views/dashboard_views.xml',
        'wizard/make_truck_booking_pdf_views.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'packers_and_movers_management/static/src/js/website_page.js',
            'packers_and_movers_management/static/src/css/website_page.css',
        ],
        'web.assets_backend': [
            'packers_and_movers_management/static/src/css/dashboard.css',
            'packers_and_movers_management/static/src/scss/style.scss',
            'packers_and_movers_management/static/src/js/lib/chart_bundle.js',
            'packers_and_movers_management/static/src/js/dasboard_action.js',
            'packers_and_movers_management/static/src/xml/dashboard_templates.xml'
        ]
    },
    'external_dependencies': {
        'python': ['geopy'],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
