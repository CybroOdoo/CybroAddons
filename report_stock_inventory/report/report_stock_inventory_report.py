# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import datetime
from odoo import api, models, _
from odoo.exceptions import UserError


class InventoryReportPDF(models.AbstractModel):
    """Abstract model for generating PDF reports for stock inventory."""
    _name = "report.report_stock_inventory.report_stock_pdf"

    @api.model
    def _get_report_values(self, docids, data):
        """Get the values for generating the stock inventory report.
            :param docids: Document IDs.
            :param data: Dictionary containing data for generating the report.
            :return: Dictionary with report data."""
        quantities_at_date = 0
        category_ids = data.get('category', [])
        if category_ids:
            query = """
                WITH RECURSIVE CategoryHierarchy AS (
                    SELECT id FROM product_category WHERE id IN %s
                    UNION ALL 
                    SELECT c.id FROM product_category c 
                    JOIN CategoryHierarchy ch ON c.parent_id = ch.id
                ) SELECT DISTINCT id FROM CategoryHierarchy
            """
            self.env.cr.execute(query, (tuple(category_ids),))
            all_cat_ids = [r[0] for r in self.env.cr.fetchall()]
            products = self.env['product.product'].search(
                [('categ_id', 'in', all_cat_ids),
                 ('is_storable', '=', True)])
        else:
            products = self.env['product.product'].search(
                [('is_storable', '=', True)])
        grouped_data = {}
        for val in products:
            rec = val.with_context({'location': data.get('location'),
                                    'to_date': data.get('date')})
            if data.get('location'):
                stock = self.env['stock.quant'].search(
                    [('product_id', '=', rec.id),
                     ('location_id', 'in', data['location']),
                     ('location_id.usage', '=', 'internal'),
                     ('company_id', '=', self.env.company.id)])
            else:
                stock = self.env['stock.quant'].search(
                    [('product_id', '=', rec.id),
                     ('location_id.usage', '=', 'internal'),
                     ('company_id', '=', self.env.company.id)])
            for quant_id in stock:
                key = (quant_id.product_id.id, quant_id.location_id.id)
                if key not in grouped_data:
                    grouped_data[key] = {
                        'product': quant_id.product_id,
                        'location': quant_id.location_id.display_name,
                        'qty_available': 0.0,
                        'uom_id': quant_id.product_uom_id.name
                    }
                grouped_data[key]['qty_available'] += quant_id.available_quantity

        product_dict = list(grouped_data.values())

        if not product_dict:
            raise UserError(_("No data found for the selected criteria."))

        return {
            'docs': product_dict,
            'doc_quantities': quantities_at_date,
            'loc_name': data.get('loc_name', ''),
            'categ_name': data.get('categ_name', ''),
            'report_date': datetime.date.today().strftime('%d-%m-%Y'),
            'inventory_date': data.get('inventory_date', '')
        }
