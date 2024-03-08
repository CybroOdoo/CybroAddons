# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
#############################################################################
from odoo import api, fields, models


class LabAppointmentLines(models.Model):
    """
        This class represents Lab Appointment Lines, which are individual
        tests associated with a Lab Appointment.
    """
    _name = 'lab.appointment.lines'
    _description = 'Lab Appointment '

    lab_test_id = fields.Many2one('lab.test', string="Test")
    cost = fields.Float(string="Cost", help="Cost of the lab test")
    requesting_date = fields.Date(string="Date",
                                  help="Requesting date of lab test")
    test_line_appointment_id = fields.Many2one('lab.appointment',
                                               string="Appointment")

    @api.onchange('lab_test_id')
    def cost_update(self):
        """
           Update the 'cost' field when a Lab Test is selected.
           :param self: The record itself.
        """
        if self.lab_test_id:
            self.cost = self.lab_test_id.test_cost
