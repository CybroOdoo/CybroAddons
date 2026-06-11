# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
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
from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    def sale_get_order(self, force_create=False, update_pricelist=False):
        """
        Override to prevent pricelist updates on confirmed orders.
        This fixes the migration issue from Odoo 16 to 17 where
        confirmed orders cannot have their pricelist changed.
        """
        # Get the sale order from session
        sale_order_id = request.session.get('sale_order_id')
        if sale_order_id:
            sale_order_sudo = request.env['sale.order'].sudo().browse(sale_order_id)
            # If order exists and is confirmed (sale/done), don't update pricelist
            if sale_order_sudo.exists() and sale_order_sudo.state not in ('draft', 'sent',
                                                                          'cancel'):
                # For confirmed orders, skip the parent's update logic
                # Just return the order without modifications
                if not request.website.is_public_user():
                    sale_order_sudo = sale_order_sudo.with_context(
                        not_self_saleperson=True
                    )
                return sale_order_sudo
        # For draft orders or new orders, use the standard flow
        return super(Website, self).sale_get_order(
            force_create=force_create,
            update_pricelist=update_pricelist
        )