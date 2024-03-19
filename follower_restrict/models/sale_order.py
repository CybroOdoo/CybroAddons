# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import models


class SaleOrder(models.Model):
    """Inherits the sale order for disable the follower"""
    _inherit = 'sale.order'

    def action_confirm(self):
        """Check whether 'Disable Follower' is enabled.
            Check whether user and customer are same.
            If not unsubscribe the customer from followers list"""
        result = super(SaleOrder, self).action_confirm()
        if self.env['ir.config_parameter'].get_param(
                "follower_restrict.disable_followers"):
            user_partner = self.user_id.partner_id.id if self.user_id else False
            unsubscribe_followers = [follower.partner_id.id for follower in
                                     self.message_follower_ids if
                                     follower.partner_id.id != user_partner]
            if unsubscribe_followers:
                self.message_unsubscribe(unsubscribe_followers)
        return result
