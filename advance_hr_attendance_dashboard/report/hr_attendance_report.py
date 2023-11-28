# -- coding: utf-8 --
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys (<https://www.cybrosys.com>)
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
###############################################################################
from odoo import api, models


class ReportHrAttendance(models.AbstractModel):
    """This is an abstract model for the Attendance Report of Employees."""
    _name = 'report.advance_hr_attendance_dashboard.report_hr_attendance'
    _description = 'Attendance Report  of Employees'

    @api.model
    def _get_report_values(self, doc_ids, data=None):
        """Get the report values for the Attendance Report."""
        return {
            'doc_model': 'hr.attendance',
            'data': data,
            'self': self,
        }
