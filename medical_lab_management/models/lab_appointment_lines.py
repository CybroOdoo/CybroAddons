# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class LabAppointmentLines(models.Model):
    """
        This class represents Lab Appointment Lines, which are individual
        tests associated with a Lab Appointment.
    """
    _name = 'lab.appointment.lines'
    _description = 'Lab Appointment Line'

    lab_test_id = fields.Many2one('lab.test', string="Test")
    cost = fields.Float(help="Cost of the lab test")
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
