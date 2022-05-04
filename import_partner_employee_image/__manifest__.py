# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ijaz (<https://www.cybrosys.com>)
#
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
    'name': "Import Employee/Partner Image",
    'version': '14.0.1.0.0',
    'category': 'Human Resources',
    'summary': """Import Partner/Employee Image From Url and Local storage using CSV and XLSX Files""",
    'description': """Import Partner/Employee Image From Url and Local storage using CSV and XLSX Files""",
    'author': "Frontware, Cybrosys Techno Solutions",
    'company': 'Frontware, Cybrosys Techno Solutions',
    'maintainer': 'Frontware, Cybrosys Techno Solutions',
    'website': "https://github.com/Frontware/CybroAddons",
    'depends': ['hr', 'contacts'],
    'data': ['views/import_employee_image.xml',
             'views/import_partner_image.xml',
             'security/ir.model.access.csv',
             ],
    'license': 'AGPL-3',
    'images': ['static/description/banner.png'],
    'application': False,
    'installable': True,
    'auto_install': False,
}
