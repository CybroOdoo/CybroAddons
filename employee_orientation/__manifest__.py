# -*- coding: utf-8 -*-
###################################################################################
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': "Employee Orientation & Training",
    'version': '12.0.1.0.0',
    'category': "Generic Modules/Human Resources",
    'summary': """Employee Orientation/Training Program""",
    'description':'Complete Employee Orientation/Training Program',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'hr'],
    'data': [
        'views/orientation_checklist_line.xml',
        'views/employee_orientation.xml',
        'views/orientation_checklist.xml',
        'views/orientation_checklists_request.xml',
        'views/orientation_checklist_sequence.xml',
        'views/orientation_request_mail_template.xml',
        'views/print_pack_certificates_template.xml',
        'views/report.xml',
        'views/employee_training.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
