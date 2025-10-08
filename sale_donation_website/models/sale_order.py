# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    """Inheriting sale order"""
    _inherit = 'sale.order'

    donation_ids = fields.Many2many('donation.rule', string="Donation",
                                    help="Donation choose from rules")
    donation_amount = fields.Float(string='Donation Amount',
                                   compute="_compute_donation_amount",
                                   help='Donation Amount enter', default=0.00)

    @api.depends('donation_ids')
    def _compute_donation_amount(self):
        """To compute donation amount"""
        if self.donation_ids:
            for rec in self.donation_ids:
                self.donation_amount = self.donation_amount + rec.amount
        else:
            self.donation_amount = 0.00

    def action_confirm(self):
        """To create donation lines when confirming a sale order"""
        res = super(SaleOrder, self).action_confirm()
        donation_product = self.env['product.product'].search(
            [('name', '=', 'Donate')])
        for donation in self.donation_ids:
            if donation_product in self.order_line.mapped('product_id'):
                values = {
                    'partner_id': self.partner_id.id,
                    'sale': self.name,
                    'donation': donation.id,
                    'date': self.date_order,
                    'donated_amount': donation.amount,
                    'website': self.website_id.id
                }
                donation.env['donation.lines'].create(values)
        return res
