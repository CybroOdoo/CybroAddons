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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EventManagementCatering(models.Model):
    """Model for creating catering services"""
    _name = 'event.management.catering'
    _description = "Event Management"

    name = fields.Char(string="Name", readonly=True,
                       help="Name of the catering service.")
    date = fields.Date(string="Date", default=fields.Date.today, readonly=True,
                       help="Date of the catering service.")
    start_date = fields.Datetime(string="Start date", readonly=True,
                                 help="Start date and time of the catering"
                                      " service.")
    end_date = fields.Datetime(string="End date", readonly=True,
                               help="End date and time of the catering "
                                    "service.")
    catering_works_ids = fields.One2many('event.catering.work', 'catering_id',
                                         string="Catering Works",
                                         help="List of catering works "
                                              "associated with this service.")
    state = fields.Selection([('open', 'Open'), ('done', 'Done')],
                             string="State", default="open",
                             help="State of the catering service.")
    note = fields.Text(string="Terms and conditions",
                       help="Additional notes or terms for the catering"
                            " service.")
    price_subtotal = fields.Float(string='Total',
                                  compute='_compute_price_subtotal',
                                  readonly=True, store=True,
                                  help="Total cost calculated based on"
                                       " catering works.")
    parent_event_id = fields.Many2one('event.management',
                                      string="Event", readonly=True,
                                      help="Parent event associated with "
                                           "the catering service.")
    catering_id = fields.Integer(string="Catering Id",
                                 help="Unique identifier for the catering "
                                      "service.")
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id,
                                  help="Currency associated with the company "
                                       "for pricing.")
    event_type_id = fields.Many2one('event.management.type',
                                    string="Event Type", readonly=True,
                                    help="Type of the event associated with "
                                         "the catering service.")

    @api.depends('catering_works_ids')
    def _compute_price_subtotal(self):
        """Compute function for calculating sub total"""
        total = 0
        for items in self.catering_works_ids:
            total += items.quantity * items.amount
        self.price_subtotal = total

    def action_catering_done(self):
        """ Button action for state change to Done"""
        for items in self.catering_works_ids:
            if items.work_status == 'open':
                raise UserError(_("Catering works are pending"))
        related_product = self.env.ref(
            'event_catering.catering_service_product').id
        for items in self.sudo().parent_event_id.service_line_ids:
            if items.id == self.sudo().catering_id:
                items.sudo().write({'amount': self.price_subtotal,
                                    'state': 'done',
                                    'related_product_id': related_product})
        self.state = "done"
