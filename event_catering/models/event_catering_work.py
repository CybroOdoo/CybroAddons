# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class EventCateringWorks(models.Model):
    """Deals with catering works"""
    _name = 'event.catering.work'
    _description = "Catering Works"

    service_id = fields.Many2one('product.product', string="Services",
                                 required=True,
                                 help="Select the catering service for this"
                                      " work.")
    quantity = fields.Float(string="Quantity", default=1,
                            help="Enter the quantity of catering services "
                                 "provided.")
    amount = fields.Float(string="Amount",
                          help="Enter the cost of a single unit of the catering"
                               " service.")
    sub_total = fields.Float(string="Sub Total", compute="_compute_sub_total",
                             readonly=True,
                             help="Total cost calculated based on quantity and"
                                  " amount.")
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id,
                                  help="Currency associated with the company"
                                       " for pricing.")
    catering_id = fields.Many2one('event.management.catering',
                                  string="Catering Id",
                                  help="Link this work to the main catering"
                                       " management.")
    work_status = fields.Selection([('open', 'Open'), ('done', 'Done')],
                                   string="Work Status",
                                   default='open',
                                   help="Status of the catering work.")

    @api.onchange('service_id')
    def _onchange_service_id(self):
        """Update the amount based on service"""
        self.amount = self.service_id.lst_price

    @api.depends('quantity', 'amount')
    def _compute_sub_total(self):
        """Function to calculate sub total"""
        for rec in self:
            rec.sub_total = rec.quantity * rec.amount

    def action_work_completed(self):
        """Button action for completed works"""
        if self.catering_id.state == "open":
            self.work_status = 'open'

    def action_not_completed(self):
        """Button action for non completed works"""
        if self.catering_id.state == "open":
            self.work_status = 'done'
