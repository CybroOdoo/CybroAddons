# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ADARSH K (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class EventBookingLine(models.Model):
    """Model that handles the event booking form"""
    _name = "event.booking.line"
    _description = "Hotel Event Line"
    _rec_name = 'event_id'

    booking_id = fields.Many2one("room.booking", string="Booking",
                                 help="Choose room booking reference",
                                 ondelete="cascade")
    event_id = fields.Many2one('event.event', string="Event",
                               help="Choose the Event")
    ticket_id = fields.Many2one('product.product', string="Ticket",
                                help="Choose the Ticket Type",
                                domain=[('service_tracking', '=', 'event')]
                                )
    description = fields.Char(string='Description', help="Detailed "
                                                         "description of the "
                                                         "event",
                              related='event_id.display_name')
    uom_qty = fields.Float(string="Quantity", default=1,
                           help="The quantity converted into the UoM used by "
                                "the product")
    uom_id = fields.Many2one('uom.uom', readonly=True,
                             string="Unit of Measure",
                             related='ticket_id.uom_id', help="This will set "
                                                              "the unit of"
                                                              " measure used")
    price_unit = fields.Float(related='ticket_id.lst_price', string='Price',
                              digits='Product Price',
                              help="The selling price of the selected ticket.")
    tax_ids = fields.Many2many('account.tax',
                               'hotel_event_order_line_taxes_rel',
                               'event_id',
                               'tax_id', related='ticket_id.taxes_id',
                               string='Taxes',
                               help="Default taxes used when selling the event"
                                    "tickets.",
                               domain=[('type_tax_use', '=', 'sale')])
    currency_id = fields.Many2one(
        related='booking_id.pricelist_id.currency_id', string='Currency',
        help='The currency used', store=True, precompute=True)
    price_subtotal = fields.Float(string="Subtotal",
                                  compute='_compute_price_subtotal',
                                  help="Total Price Excluding Tax", store=True)
    price_tax = fields.Float(string="Total Tax",
                             compute='_compute_price_subtotal',
                             help="Tax Amount", store=True)
    price_total = fields.Float(string="Total",
                               compute='_compute_price_subtotal',
                               help="Total Price Including Tax", store=True)
    state = fields.Selection(related='booking_id.state',
                             string="Order Status",
                             help="State of Room Booking", copy=False)

    @api.depends('uom_qty', 'price_unit', 'tax_ids','currency_id')
    def _compute_price_subtotal(self):
        """Compute the amounts of the room booking line."""
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            self.env['account.tax']._add_tax_details_in_base_line(base_line, self.env.company)
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.price_total = base_line['tax_details']['raw_total_included_currency']
            line.price_tax = line.price_total - line.price_subtotal
            if self.env.context.get('import_file',
                                    False) and not self.env.user. \
                    user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_recordset(
                    ['invoice_repartition_line_ids'])

    def _prepare_base_line_for_taxes_computation(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            **{
                'tax_ids': self.tax_ids,
                'quantity': self.uom_qty,
                'partner_id': self.booking_id.partner_id,
                'currency_id': self.currency_id,
            },
        )