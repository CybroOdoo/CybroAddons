"""Machine Work order"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
    """This is used for the machine work order"""
    _name = 'machine.workorder'
    _description = "Machine Work Order"
    _rec_name = "work_order_id"

    work_order_id = fields.Many2one('machine.service', string="Work Order",
                                    help="Work order name for machine")
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help="Customer for the work order")
    date = fields.Date(string="Date", help="Work order date")
    priority = fields.Selection(
        [('low', 'Low'), ('high', 'High'), ('middle', 'Middle')],
        string="Priority", help="Work Order Priority")
    scheduled_date = fields.Date(string='Scheduled Date',
                                 help="scheduled date of work order")
    planned_end_date = fields.Date(string='Planned End date',
                                   help="Work order end date")
    duration = fields.Float(string='Duration', help="Wok order duration")
    start_date = fields.Date(string='Start Date',
                             help="Start date of work order")
    end_date = fields.Date(string='End Date', help="End date of the work order")
    hours_worked = fields.Float(string="Hours Spent",
                                help="Total hours spent for work order")
