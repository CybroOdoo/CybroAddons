# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class SaleOrderAvataxCompat(models.Model):
    """Compatibility shim for account_avatax_sale enterprise module.

    This model extension adds the field as a simple False-by-default
    computed field so that all templates referencing ``doc.is_avatax`` or
    ``order.is_avatax`` work correctly without the full AvaTax module.
    """
    _inherit = 'sale.order'

    is_avatax = fields.Boolean(
        string='Uses AvaTax',
        compute='_compute_is_avatax_compat',
        store=False, help="Use AvaTax compat for this order."
    )

    @api.depends('fiscal_position_id')
    def _compute_is_avatax_compat(self):
        """Always return False — this database does not use AvaTax."""
        for order in self:
            order.is_avatax = False
