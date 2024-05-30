# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana kp(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from markupsafe import Markup
from odoo import models, fields, _


class StockPicking(models.Model):
    """This class inherits from the base stock picking model in Odoo and allows
     for additional customization and functionality to be added
     to picking operations. """
    _inherit = "stock.picking"

    is_batch = fields.Boolean(
        "Is Batch", store=True,
        default=False, help="Is batch processing or not")

    def send_to_shipper(self):
        """ Overriding function for adding to check condition
         for batch transfer """
        self.ensure_one()
        partner_id = self.partner_id.id
        carrier_id = self.carrier_id.id
        filtered_picking_ids = self.batch_id.picking_ids.filtered(
            lambda
                x: x.partner_id.id == partner_id and x.carrier_id.id == carrier_id)
        if self.batch_id and len(filtered_picking_ids) > 1:
            self._batch_send_to_shipper()
        else:
            res = self.carrier_id.send_shipping(self)[0]
            if self.carrier_id.free_over and self.sale_id:
                amount_without_delivery = self.sale_id._compute_amount_total_without_delivery()
                if self.carrier_id._compute_currency(self.sale_id,
                                                     amount_without_delivery,
                                                     'pricelist_to_company') >= self.carrier_id.amount:
                    res['exact_price'] = 0.0
            self.carrier_price = res['exact_price'] * (
                    1.0 + (self.carrier_id.margin / 100.0))
            if res['tracking_number']:
                related_pickings = self.env[
                    'stock.picking'] if self.carrier_tracking_ref and res[
                    'tracking_number'] in self.carrier_tracking_ref else self
                accessed_moves = previous_moves = self.move_ids.move_orig_ids
                while previous_moves:
                    related_pickings |= previous_moves.picking_id
                    previous_moves = previous_moves.move_orig_ids - accessed_moves
                    accessed_moves |= previous_moves
                accessed_moves = next_moves = self.move_ids.move_dest_ids
                while next_moves:
                    related_pickings |= next_moves.picking_id
                    next_moves = next_moves.move_dest_ids - accessed_moves
                    accessed_moves |= next_moves
                without_tracking = related_pickings.filtered(
                    lambda p: not p.carrier_tracking_ref)
                without_tracking.carrier_tracking_ref = res['tracking_number']
                for p in related_pickings - without_tracking:
                    p.carrier_tracking_ref += "," + res['tracking_number']
            order_currency = self.sale_id.currency_id or self.company_id.currency_id
            msg = _(
                "Shipment sent to carrier %(carrier_name)s for shipping with tracking number %(ref)s",
                carrier_name=self.carrier_id.name,
                ref=self.carrier_tracking_ref) + \
                  Markup("<br/>") + \
                  _("Cost: %(price).2f %(currency)s",
                    price=self.carrier_price,
                    currency=order_currency.name)
            self.message_post(body=msg)
            self._add_delivery_cost_to_so()

    def _batch_send_to_shipper(self):
        """ Method to batch send shipments to the shipper.
            This method is responsible for sending shipments to the designated
            carrier. It calculates the shipping cost, updates tracking
            information, and posts messages related to the shipment. """
        partner_id = self.partner_id.id
        carrier_id = self.carrier_id.id
        filtered_picking_ids = self.batch_id.picking_ids.filtered(
            lambda
                x: x.partner_id.id == partner_id and x.carrier_id.id == carrier_id)
        res = self.carrier_id.send_shipping(self)[0]
        if self.carrier_id.free_over and self.sale_id:
            amount_without_delivery = self.sale_id._compute_amount_total_without_delivery()
            if self.carrier_id._compute_currency(self.sale_id,
                                                 amount_without_delivery,
                                                 'pricelist_to_company') >= self.carrier_id.amount:
                res['exact_price'] = 0.0
        self.carrier_price = res['exact_price'] * (
                1.0 + (self.carrier_id.margin / 100.0))
        if res['tracking_number']:
            related_pickings = self.env[
                'stock.picking'] if self.carrier_tracking_ref and res[
                'tracking_number'] in self.carrier_tracking_ref else self
            accessed_moves = previous_moves = self.move_ids.move_orig_ids
            while previous_moves:
                related_pickings |= previous_moves.picking_id
                previous_moves = previous_moves.move_orig_ids - accessed_moves
                accessed_moves |= previous_moves
            accessed_moves = next_moves = self.move_ids.move_dest_ids
            while next_moves:
                related_pickings |= next_moves.picking_id
                next_moves = next_moves.move_dest_ids - accessed_moves
                accessed_moves |= next_moves
            num = 0
            for pick in filtered_picking_ids:
                if not pick.carrier_tracking_ref:
                    tracking_numbers = res['tracking_number'].split(',')
                    if num < len(tracking_numbers):
                        pick.carrier_tracking_ref = tracking_numbers[num]
                        num += 1
                    else:
                        pick.carrier_tracking_ref = res['tracking_number']
                    order_currency = pick.sale_id.currency_id or pick.company_id.currency_id
                    msg = _(
                        "Shipment sent to carrier %(carrier_name)s for shipping with tracking number %(ref)s",
                        carrier_name=pick.carrier_id.name,
                        ref=pick.carrier_tracking_ref) + \
                          Markup("<br/>") + \
                          _("Cost: %(price).2f %(currency)s",
                            price=pick.carrier_price,
                            currency=order_currency.name)
                    pick.message_post(body=msg)
                    pick._add_delivery_cost_to_so()
