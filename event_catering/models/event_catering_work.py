# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Subina (odoo@cybrosys.com)
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


class EventCateringWork(models.Model):
    """
    This class is for creating catering works.
    it contains fields and functions for the model.
    Methods:
        _onchange_service_id(self):
            calculate value of amount field when change the service_id
        _compute_sub_total(self):
            computes sub_total field
    """
    _name = 'event.catering.work'
    _description = "Event Catering Work"

    service_id = fields.Many2one('product.product', string="Services",
                                 required=True, help="Choose the services")
    quantity = fields.Float(string="Quantity", default=1,
                            help="How many quantity consumed")
    amount = fields.Float(string="Amount", help="Amount per quantity")
    sub_total = fields.Float(string="Sub Total", compute="_compute_sub_total",
                             readonly=True, help="Shows subtotal")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id
                                  .currency_id.id,
                                  required=True, help='Currency in which '
                                                      'payments will be done')
    catering_id = fields.Many2one('event.management.catering',
                                  string="Catering Id",
                                  help="Select the catering")
    work_status = fields.Selection([('open', 'Open'), ('done', 'Done')],
                                   string="Work Status", default='open',
                                   help="Shows the current status of catering")

    @api.onchange('service_id')
    def _onchange_service_id(self):
        """ Function for calculate amount field when change
         service_id field """
        self.amount = self.service_id.lst_price

    @api.depends('quantity', 'amount')
    def _compute_sub_total(self):
        """ Computes sub_total field when quantity or amount changes """
        for rec in self:
            rec.sub_total = rec.quantity * rec.amount
