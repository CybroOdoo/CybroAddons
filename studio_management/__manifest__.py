# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Digital Studio Management',
    'version': '10.0.1.0.0',
    'summary': """Easily Manage Multimedia/Studio Industry""",
    'description': """Easily Manage Multimedia/Studio Industry""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'category': 'Industries',
    'depends': ['base', 'report'],
    'license': 'LGPL-3',
    'data': [
        'security/studio_security.xml',
        'wizard/studio_report_wizard.xml',
        'views/session_view.xml',
        'views/studio_report.xml',
        'views/session_type.xml',
        'views/editing_works.xml',
        'views/studio_sequence.xml',
        'views/studio_views.xml',
        'report/report_template.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
