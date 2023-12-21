# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class EmployeeChecklist(models.Model):
    """Create an 'employee_checklist' model to incorporate
    details about document types"""
    _name = 'employee.checklist'
    _inherit = 'mail.thread'
    _description = "Employee Checklist"

    name = fields.Char(string='Document Name', copy=False, required=1,
                       help="Enter Document Name")
    document_type = fields.Selection([('entry', 'Entry Process'),
                                      ('exit', 'Exit Process'),
                                      ('other', 'Other')],
                                     string='Checklist Type', required=1,
                                     help="Select checklist type for document")

    def name_get(self):
        """Function to obtain the names '_en,' '_ex,' or '_ot'
        for entry, exit, and other."""
        result = []
        for each in self:
            if each.document_type == 'entry':
                name = each.name + '_en'
            elif each.document_type == 'exit':
                name = each.name + '_ex'
            elif each.document_type == 'other':
                name = each.name + '_ot'
            result.append((each.id, name))
        return result
