# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2015-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Sreejith P(<http://www.cybrosys.com>)
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
    'name': "Advance Salary",
    'version': "8.0.1.0.0",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'summary': 'Advance salary payment option to the Employee.',
    'website': 'https://www.cybrosys.com',
    'license': "AGPL-3",
    'category': "Human resources",
    'depends': ['hr', 'hr_payroll', 'hr_contract'],
    'data': [
        "security/ir.model.access.csv",
        "views/salary_structure_view.xml",
        "views/salary_advance_menu.xml",
        "views/advance_rule_menu.xml",
        "views/journal_entry.xml",
    ],
    'installable': True,
    'active': False,
    'images': ['static/description/banner.jpg'],
    'auto_install': False,
}
