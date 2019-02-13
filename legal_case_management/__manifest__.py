# -*- coding: utf-8 -*-
###################################################################################
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Lesser General Public License(LGPLv3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Legal Case Management',
    'summary': """Module for managing LEGAL Processes""",
    'version': '12.0.1.0.0',
    'description': """ALL LEGAL FIRM BASED PROBLEMS GET SOLVED HERE""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'category': 'Tools',
    'depends': ['base', 'hr_payroll', 'document', 'hr'],
    'license': 'LGPL-3',
    'data': [
        'views/legal_views.xml',
        'views/res_partner_views.xml',
        'views/sequence.xml',
        'security/ir.model.access.csv',

    ],
    'demo': [],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
}
