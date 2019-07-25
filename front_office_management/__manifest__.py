# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha P P(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': "Front Office Management",
    'version': '12.0.1.0.0',
    'summary': """Manage Front Office Operations:Visitors, Devices Carrying Register, Actions""",
    'description': """Helps You To Manage Front Office Operations""",
    'author': "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'company': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'category': 'Industries',
    'depends': ['base', 'hr'],
    'data': [
        'views/fo_visit.xml',
        'views/fo_visitor.xml',
        'views/fo_property_counter.xml',
        'report/report.xml',
        'report/fo_property_label.xml',
        'report/fo_visitor_label.xml',
        'report/visitors_report.xml',
        'security/fo_security.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
