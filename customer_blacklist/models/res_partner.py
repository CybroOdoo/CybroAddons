# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class ResPartner(models.Model):
    """
    Extend the base ResPartner model to include additional features.

    This class inherits from the base ResPartner model and adds functionality
    to mark customers as blacklisted.
    """
    _inherit = 'res.partner'

    blacklisted_partner = fields.Boolean(string="Blacklist Partner",
                                         help="Enable this option to mark the customer as blacklisted.")

    def write(self, vals):
        """If a partner is blacklisted, clear cart and wishlist"""
        res = super().write(vals)
        if vals.get('blacklisted_partner'):
            for partner in self:
                sale_orders = self.env['sale.order'].search([
                    ('partner_id', '=', partner.id),
                    ('state', '=', 'draft'),
                    ('website_id', '!=', False)
                ])
                for order in sale_orders:
                    order.order_line.unlink()
                wishlist = self.env['product.wishlist'].search([
                    ('partner_id', '=', partner.id)
                ])
                wishlist.unlink()
        return res
