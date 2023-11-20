# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
###############################################################################
{
    'name': "Legal Case Management Dashboard",
    'version': '16.0.1.0.0',
    'category': 'Services',
    'summary': """Legal Case Management Dashboard to get an overview of 
     legal case management module.""",
    'description': """This module helps you to view an detailed overview of all
     working of the Legal Case Management management module with graphs and 
     dashboard clickable cards in odoo 16.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['legal_case_management'],
    'data': [
        'views/legal_case_management_dashboard_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'legal_case_management_dashboard/static/src/js/dashboard_action.js',
            'legal_case_management_dashboard/static/src/xml'
            '/dashboard_template.xml',
            'legal_case_management_dashboard/static/src/css/style.css',
            "https://www.gstatic.com/charts/loader.js",
            "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.4/Chart.js",
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
