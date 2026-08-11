# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anshad Ahammed M (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (
#    OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from datetime import datetime
from odoo import api, models


class InventoryReportPDF(models.AbstractModel):
    """Abstract model for generating PDF reports for stock inventory."""
    _name = "report.report_stock_inventory.report_stock_pdf"

    @api.model
    def _get_report_values(self, docids, data):
        """Get the values for generating the stock inventory report."""
        quantities_at_date = 0
        if data['category']:
            products = self.env['product.product'].search(
                [('categ_id', 'child_of', data['category']),
                 ('is_storable', '=', True)
                 ])
        else:
            products = self.env['product.product'].search(
                [('is_storable', '=', True)
                 ])

        # Build moves search domain up to the target date
        domain_moves = [
            ('product_id', 'in', products.ids),
            ('state', '=', 'done'),
            ('company_id', '=', self.env.company.id)
        ]
        if data['date']:
            domain_moves.append(('date', '<=', data['date']))

        if data['location']:
            domain_moves.append('|')
            domain_moves.append(('location_id', 'in', data['location']))
            domain_moves.append(('location_dest_id', 'in', data['location']))

        moves = self.env['stock.move'].search(domain_moves)

        # Find allowed internal locations
        loc_domain = [('usage', '=', 'internal'), ('company_id', 'in', [self.env.company.id, False])]
        if data['location']:
            loc_domain.append(('id', 'in', data['location']))
        internal_locs = self.env['stock.location'].search(loc_domain)
        internal_loc_ids = set(internal_locs.ids)

        # Compute stock balances per product and location
        balances = {}
        for move in moves:
            prod_id = move.product_id.id
            qty = move.product_qty
            src_id = move.location_id.id
            dest_id = move.location_dest_id.id

            if src_id in internal_loc_ids:
                key = (prod_id, src_id)
                balances[key] = balances.get(key, 0.0) - qty

            if dest_id in internal_loc_ids:
                key = (prod_id, dest_id)
                balances[key] = balances.get(key, 0.0) + qty

        # Prepare product_dict
        product_dict = []
        for (prod_id, loc_id), qty in balances.items():
            if qty > 0.0:  # Only show non-zero positive inventory in locations
                prod = products.filtered(lambda p: p.id == prod_id)
                if not prod:
                    prod = self.env['product.product'].browse(prod_id)
                loc = internal_locs.filtered(lambda l: l.id == loc_id)
                if not loc:
                    loc = self.env['stock.location'].browse(loc_id)
                product_dict.append({
                    'product': prod,
                    'location': loc.complete_name or loc.name or '',
                    'qty_available': qty,
                    'uom_id': prod.uom_id.name or '',
                })

        return {
            'docs': product_dict,
            'doc_quantities': quantities_at_date,
            'loc_name': data['loc_name'],
            'categ_name': data['categ_name'],
            'report_date': datetime.today().strftime('%d-%m-%Y'),
            'inventory_date': data['inventory_date']
        }
