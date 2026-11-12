# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _get_tax_details(self):
        """Return a list of dicts with the tax name and computed amount for
        each applied tax."""
        self.ensure_one()
        tax_amounts = {}
        for line in self.lines:
            if not line.tax_ids_after_fiscal_position:
                continue
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_ids_after_fiscal_position.compute_all(
                price,
                self.currency_id,
                line.qty,
                product=line.product_id,
                partner=self.partner_id,
            )
            for tax_res in taxes.get('taxes', []):
                tax_id = tax_res['id']
                if tax_id not in tax_amounts:
                    tax_amounts[tax_id] = {
                        'name': tax_res['name'],
                        'amount': 0.0,
                    }
                tax_amounts[tax_id]['amount'] += tax_res['amount']
        return list(tax_amounts.values())
