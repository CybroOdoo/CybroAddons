# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(odoo@cybrosys.com)
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
