# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
    'name': "Front Office Management",
    'version': '17.0.1.0.0',
    'summary': "Manage Front Office Operations:Visitors, Devices Carrying"
               "Register, Actions",
    'description': """Helps You To Manage Front Office Operations, Odoo 17""",
    'author': "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'company': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'category': 'Industries',
    'depends': ['base', 'hr'],
    'data': [
        'data/front_office_management_sequence.xml',
        'security/fo_security.xml',
        'security/ir.model.access.csv',
        'views/fo_visit_views.xml',
        'views/id_proof_views.xml',
        'views/fo_purpose_views.xml',
        'views/fo_visitor_views.xml',
        'views/fo_property_counter_views.xml',
        'report/front_office_management_reports.xml',
        'report/property_label_templates.xml',
        'report/visitor_label_templates.xml',
        'report/visitors_report_templates.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,

}
