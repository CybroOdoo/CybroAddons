# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _create_picking(self):
        """Let core create the picking(s) as usual. Quality alerts are
        generated automatically by stock.picking.action_confirm()."""
        res = super()._create_picking()
        for order in self:
            if any(ptype in ['product', 'consu'] for ptype in
                   order.order_line.mapped('product_id.type')):
                pickings = order.picking_ids.filtered(
                    lambda x: x.state not in ('done', 'cancel')
                    and x.picking_type_id.code == 'incoming')
                if pickings:
                    self.message_post_with_source(
                        'mail.message_origin_link',
                        render_values={
                            'self': pickings,
                            'origin': order},
                        subtype_xmlid='mail.mt_note',
                    )
        return res