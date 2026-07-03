# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class HrEmployee(models.Model):
    """Inheriting this model to compute the disciplinary action count"""
    _inherit = 'hr.employee'

    discipline_count = fields.Integer(
        compute="_compute_discipline_count",
        help="To compute the employee details based on the discipline count",
    )

    def _compute_discipline_count(self):
        """Compute the number of validated disciplinary actions per employee.

        Uses _read_group (Odoo 19+) instead of the deprecated read_group.
        """
        DisciplinaryAction = self.env['disciplinary.action']
        groups = DisciplinaryAction._read_group(
            domain=[
                ('employee_id', 'in', self.ids),
                ('state', '=', 'action'),
            ],
            groupby=['employee_id'],
            aggregates=['__count'],
        )
        # _read_group returns a list of tuples: (employee_id_record, count)
        mapping = {employee.id: count for employee, count in groups}
        for employee in self:
            employee.discipline_count = mapping.get(employee.id, 0)
