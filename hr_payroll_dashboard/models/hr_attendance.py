# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
################################################################################
from odoo import api, fields, models


class HrAttendance(models.Model):
    """
    This class extends the HR Attendance model to include additional fields
    and functionalities.
    """
    _inherit = 'hr.attendance'

    attendance_date = fields.Date(compute="_compute_attendance_date",
                                  store=True,
                                  help="The date of attendance based on the "
                                       "check-in time.")

    @api.depends('check_in')
    def _compute_attendance_date(self):
        """Compute function for the attendance date"""
        for rec in self:
            if rec.check_in:
                rec.attendance_date = rec.check_in.date()
