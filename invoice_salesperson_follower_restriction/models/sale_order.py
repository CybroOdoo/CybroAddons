# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import models


class SaleOrder(models.Model):
    """Inherit sale.order to restrict salesperson from invoice followers."""
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Override to remove salesperson from invoice followers if different
        from the sales order creator when restriction setting is enabled."""
        invoices = super()._create_invoices(
            grouped=grouped,
            final=final,
            date=date,
        )

        enable_restriction = self.env[
            'ir.config_parameter'
        ].sudo().get_param(
            'invoice_salesperson_follower_restriction.enable_restriction',
            'False',
        )
        if str(enable_restriction).lower() not in ('true', '1'):
            return invoices

        for order in self:
            if (
                order.user_id
                and order.create_uid
                and order.user_id != order.create_uid
            ):
                partner = order.user_id.partner_id
                customer_partners = (
                    order.partner_id | order.partner_id.commercial_partner_id
                )
                if partner and partner not in customer_partners:
                    order_invoices = invoices.filtered(
                        lambda inv: order in inv.line_ids.sale_line_ids.order_id
                        or (inv.invoice_origin and order.name in inv.invoice_origin)
                    )

                    for invoice in order_invoices:
                        follower = invoice.message_follower_ids.filtered(
                            lambda f: f.partner_id == partner
                            and f.partner_id not in customer_partners
                        )
                        if follower:
                            follower.sudo().unlink()

        return invoices
