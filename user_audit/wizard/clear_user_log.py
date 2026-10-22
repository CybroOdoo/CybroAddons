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
from odoo import fields, models, _
from odoo.exceptions import UserError


class ClearUserLog(models.TransientModel):
    """ Model that uses to Clear the User Audit Logs"""
    _name = "clear.user.log"
    _description = "Clear User Logs"

    full_log = fields.Boolean(string="Full Log",
                              help="Enabling we can clear full log details")
    is_read = fields.Boolean(string="Read",
                             help="Enabling we can clear all read activities")
    is_write = fields.Boolean(string="Write",
                              help="Enabling we can clear all write activities")
    is_create = fields.Boolean(string="Create",
                               help="Enabling we can clear all create "
                                    "activities")
    is_delete = fields.Boolean(string="Delete",
                               help="Enabling we can clear all delete "
                                    "activities")
    to_date = fields.Datetime(string="To Date",
                              help="Enabling we can clear all activities "
                                   "up to the date")
    model_id = fields.Many2one('ir.model', string="Object",
                               help="Clear selected model's activities")

    def action_clear_user_logs(self):
        """ Function that helps to clear the log data based
            on the criteria from the wizard"""
        if self.full_log:
            self.env['user.audit.log'].search([]).unlink()
            return

        domain = []
        operations = []
        if self.is_create:
            operations.append('create')
        if self.is_write:
            operations.append('write')
        if self.is_read:
            operations.append('read')
        if self.is_delete:
            operations.append('delete')

        if operations:
            domain.append(('operation_type', 'in', operations))
        if self.to_date:
            domain.append(('date', '<', self.to_date))
        if self.model_id:
            domain.append(('model_id', '=', self.model_id.id))

        if not domain:
            raise UserError(_("Please select at least one criteria or enable 'Full Log' to clear logs."))

        self.env['user.audit.log'].search(domain).unlink()


