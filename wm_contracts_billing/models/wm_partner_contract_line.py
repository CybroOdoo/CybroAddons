# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class WmPartnerContractLine(models.Model):
    """Contracted waste category rate line specifying collection basis and price per kg."""
    _name = 'wm.partner.contract.line'
    _description = 'Waste Management Contract Line'

    category_id = fields.Many2one(
        'wm.waste.category',
        string='Category',
        required=True,
    )
    contract_id = fields.Many2one('wm.partner.contract', string='Contract', required=True)
    product_ids = fields.Many2many(
        'product.product',
        string='Products',
        domain="[('is_waste_material', '=', True), ('wm_waste_category_id', '=', category_id)]",
    )
    contract_currency_id = fields.Many2one(
        related='contract_id.currency_id', string='Currency'
    )
    price = fields.Monetary(
        string='Rate per kg',
        currency_field='contract_currency_id',
        help="Price per kg for this waste category. Only used when the "
             "contract's Billing is 'Per Category Rate'."
    )
