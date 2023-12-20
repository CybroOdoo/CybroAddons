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
from odoo import fields, models, _


class HrEmployee(models.Model):
    """Inherit the 'hr_employee' module to add 'Documents' super button."""
    _inherit = 'hr.employee'

    document_count = fields.Integer(compute='_compute_document_count',
                                    string='# Documents',
                                    help="Get total count of Document for"
                                         " an Employee")

    def _compute_document_count(self):
        """Function to obtain the total count of documents."""
        for rec in self:
            rec.document_count = self.env['hr.employee.document'].search_count(
                [('employee_id', '=', rec.id)])

    def document_view(self):
        """Function to open the 'hr_employee_document' model."""
        self.ensure_one()
        return {
            'name': _('Documents'),
            'domain': [('employee_id', '=', self.id)],
            'res_model': 'hr.employee.document',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'help': _('''<p class="oe_view_nocontent_create">
                           Click to Create for New Documents
                        </p>'''),
            'limit': 80,
            'context': {'default_employee_id': self.id}
        }
