# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhilesh N S (odoo@cybrosys.com)
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

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    care_of_partner_id = fields.Many2one('res.partner', string='Care Of (C/O)', required=False,
                                         readonly=True,
                                         states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                         help="To address a contact in care of someone else")
    care_of_percentage = fields.Float(string='C/O Commission Percentage',
                                      readonly=True,
                                      states={'draft': [('readonly', False)], 'sent': [('readonly', False)]})
    care_of_commission = fields.Monetary(string='C/O Commission Amount', store=True, readonly=True,
                                         compute='_amount_all')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        self.care_of_partner_id = self.partner_id.care_of_partner_id
        self.care_of_percentage = self.partner_id.care_of_percentage

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """Compute the C/O Commission amounts of the SO"""
        res = super(SaleOrder, self)._amount_all()
        for order in self:
            order.update({
                'care_of_commission': order.care_of_percentage * order.amount_untaxed
            })
        return res
