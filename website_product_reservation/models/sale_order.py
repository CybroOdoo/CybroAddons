# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    """ This class extends the 'sale.order' model in Odoo.
    It adds a new state ('reserve') and introduces a boolean field
    ('is_reservation_order') to identify reservation orders.
    Methods:
        - action_make_draft: Sets the order state to 'draft' and cancels
        reservation stock for product lines.
        - action_cancel_reservation: Cancels reservation stock for product
        lines and sets the order state to 'cancel'."""
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=[('reserve', 'Reserve')],
                             string='Order State',
                             help='The state of the sale order')
    is_reservation_order = fields.Boolean(string='Reservation Order',
                                          help='Check if the order is a '
                                               'reservation order')

    def action_make_draft(self):
        """ Action method to set the order state to 'draft' and cancel
        reservation stock for product lines."""
        self.state = 'draft'
        for line in self.order_line.filtered(
                lambda line: line.product_id.type == 'product'):
            line.cancel_reservation_stock(line.picking_id)

    def action_cancel_reservation(self):
        """ Action method to cancel reservation stock for product lines and set
        the order state to 'cancel'."""
        for line in self.order_line.filtered(
                lambda line: line.product_id.type == 'product'):
            line.cancel_reservation_stock(line.picking_id)
        self.state = 'cancel'


class Company(models.Model):
    """ This class extends the 'res.company' model in Odoo.
    It adds a new field ('destination_location_id') to store the destination
    location."""
    _inherit = 'res.company'

    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        help='The destination location for products.')


class AccountConfig(models.TransientModel):
    """ This class extends the 'res.config.settings' model in Odoo.
    It adds a related field ('destination_location_id') to configure the
    destination location."""
    _inherit = "res.config.settings"

    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        related='company_id.destination_location_id',
        readonly=False,
        help='The destination location for products.')
