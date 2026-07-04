# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class PlannedWork(models.Model):
    """Model for planned work in car workshop"""
    _name = 'planned.work'
    _description = 'Planned Work in Car Workshop'

    name = fields.Char(string='Planned work', required=True,
                                  help='Planned work details')
    time_spent = fields.Float(string='Estimated Time',help='Estimated time for the work')
    work_date = fields.Datetime(string='Date',
                                help='Date of work planned:planned date')
    user_id = fields.Many2one('res.users', string='Responsible',
                              help='The responsible user')
    work_id = fields.Many2one('car.workshop', string="Work id",
                              help='The work details')
    work_cost = fields.Float(string="Service Cost",
                             help='The service cost of work')
    is_completed = fields.Boolean(string="Completed",
                                  help='If enabling this field indicates that '
                                       'this work completed')
    duration = fields.Float(string='Duration', help='Time taken for the work')
    work_date2 = fields.Datetime(string='Date',help='Date of work '
                                                    'completed/done:completed'
                                                    ' date')
    invoice_line_ids = fields.Many2many('account.move.line', 'planned_work_inv_line_rel', 'work_id', 'line_id', string='Invoice Lines')
    is_invoiced = fields.Boolean(string="Invoiced", compute='_compute_is_invoiced', store=True)

    @api.depends('invoice_line_ids.move_id.state')
    def _compute_is_invoiced(self):
        for rec in self:
            rec.is_invoiced = any(line.move_id.state != 'cancel' for line in rec.invoice_line_ids)



    @api.onchange('is_completed')
    def _onchange_is_completed(self):
        """When the work is marked as completed, copy estimated time into duration"""
        if self.is_completed:
            self.duration = self.time_spent
            self.work_date2 = fields.Datetime.now()
