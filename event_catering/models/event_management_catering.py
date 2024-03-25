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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EventManagementCatering(models.Model):
    """
    This class is for creating catering services.
    it contains fields and functions for the model.
    Methods:
        _compute_price_subtotal(self):
            computes price_subtotal field
        action_catering_done(self):
            actions to perform when clicking on the 'Done' button.
    """
    _name = 'event.management.catering'
    _description = "Event Management Catering"

    name = fields.Char(string="Name", readonly=True, help="Name of caterings")
    date = fields.Date(string="Date", default=fields.Date.today, readonly=True,
                       help="date of catering created")
    start_date = fields.Datetime(string="Start date", readonly=True,
                                 help="starting date of catering service")
    end_date = fields.Datetime(string="End date", readonly=True,
                               help="end date of catering service")
    catering_works_ids = fields.One2many('event.catering.work', 'catering_id',
                                         string="Catering Works",
                                         help="selected catering works")
    state = fields.Selection([('open', 'Open'), ('done', 'Done')],
                             string="State", default="open",
                             help="Current state of event")
    note = fields.Text(string="Terms and conditions",
                       help="Display terms and condition for this service")
    price_subtotal = fields.Float(string='Total',
                                  compute='_compute_price_subtotal',
                                  readonly=True, store=True,
                                  help="Shows the total price")
    parent_event_id = fields.Many2one('event.management', string="Event",
                                      readonly=True, help="Parent event")
    catering_id = fields.Integer(string="Catering Id",
                                 help="Catering serial no")
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  string="Currency",
                                  default=lambda self:
                                  self.env.user.company_id.currency_id,
                                  help="Select currency")
    event_type_id = fields.Many2one('event.management.type',
                                    string="Event Type", readonly=True,
                                    help="Select the type of event")

    @api.depends('catering_works_ids')
    def _compute_price_subtotal(self):
        """ Computes price_subtotal field """
        total = 0
        for items in self.catering_works_ids:
            total += items.quantity * items.amount
        self.price_subtotal = total

    def action_catering_done(self):
        """ Function for the 'Done' button to change the state to 'Done'. """
        for items in self.catering_works_ids:
            if items.work_status == 'open':
                raise UserError(_("Catering works are pending"))
        for items in self.sudo().parent_event_id.service_line_ids:
            if items.id == self.sudo().catering_id:
                items.sudo().write({
                    'amount': self.price_subtotal,
                    'state': 'done',
                    'related_product_id': self.env.ref(
                        'event_catering.catering_service_product').id})
        self.state = "done"
