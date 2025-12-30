# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class MachineWorkOrder(models.Model):
    """This model is used to manage machine work orders."""
    _name = 'machine.workorder'
    _description = "Machine Work Order"
    _rec_name = "work_order_id"

    work_order_id = fields.Many2one('machine.service', string="Work Order",
                                    help="The service associated with this work order.")
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help="The customer requesting the work order.")
    date = fields.Date(string="Date", help="The date when the work order is created.")
    priority = fields.Selection([('high', 'High'), ('normal', 'Normal'),('low', 'Low')],
                                string="Priority",
                                help="The priority level of the work order.")
    scheduled_date = fields.Date(string='Scheduled Date',
                                 help="The scheduled start date for the work order.")
    planned_end_date = fields.Date(string='Planned End Date',
                                   help="The planned completion date of the work order.")
    duration = fields.Float(string='Duration',
                            help="The estimated duration of the work order in hours.")
    start_date = fields.Date(string='Start Date',
                             help="The actual start date of the work order.")
    end_date = fields.Date(string='End Date',
                           help="The actual end date of the work order.")
    hours_worked = fields.Float(string="Hours Spent",
                                help="The total number of hours worked on this order.")
    repair_id = fields.Many2one('machine.repair', string="Repair",
                                            help="Reference to the related machine repair record.")
