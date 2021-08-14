# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Employee Covid Vaccination Details',
    'version': '14.0.1.0.0',
    'summary': """Employee Covid Vaccination Details""",
    'description': "Employee Covid Vaccination Details, Employee Covid Vaccination Detail,"
                   "Employee Vaccination Details, Vaccination Details, Vaccination, Covid Vaccination, Covid Vaccine,"
                   "Vaccine, Covid, Covid19, Corona",
    'category': 'Generic Modules/Human Resources',
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/vaccine_info.xml',
        'views/vaccine_centre.xml',
        'views/hr_employee.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
