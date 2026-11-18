# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE,ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from datetime import datetime, time
from odoo import fields, models
from odoo.exceptions import ValidationError


class BomUsageReport(models.TransientModel):
    """Model to generate PDF reports regarding product usage in BOMs."""
    _name = 'bom.usage.details'
    _description = "BOM Usage Details"

    product_ids = fields.Many2many(
        'product.product',
        string='Products',
        domain=lambda self: self._get_product_domain(),
        help="Select the products used in the BOM.")
    from_date = fields.Date(
        help="Starting date of the report.")
    to_date = fields.Date(
        default=fields.Date.today,
        help="Ending date of the report.")
    un_build_orders = fields.Boolean(
        string='Reduce Unbuild Orders',
        help="Deduct unbuild orders from the report.")

    def _get_product_domain(self):
        """Domain to show products available in the active company."""
        return [('company_id', 'in', [False, self.env.company.id])]

    def action_get_report(self):
        """Button action to get the report data and pass to the report."""
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValidationError(
                self.env._("The 'From Date' must be earlier than or equal to 'To Date'."))

        product_ids = self.product_ids.ids or self.env[
            'product.product'].search([
                ('company_id', 'in', [False, self.env.company.id])
            ]).ids
        if not product_ids:
            raise ValidationError(self.env._("No products found."))

        product_tuple = tuple(product_ids)
        company_id = self.env.company.id
        from_datetime = datetime.combine(
            self.from_date, time.min) if self.from_date else None
        to_datetime = datetime.combine(
            self.to_date, time.max) if self.to_date else None

        self.env.flush_all()

        # Manufacturing query with component UoM and date_finished
        mrp_query = """
            SELECT mrp_production.product_id AS parent_product_id,
                   stock_move.product_id AS child_product_id,
                   stock_move.uom_id AS uom,
                   SUM(COALESCE(stock_move.product_qty, stock_move.product_uom_qty, 0)) AS child_product_used
            FROM mrp_production
            INNER JOIN stock_move ON mrp_production.id = stock_move.raw_material_production_id
            WHERE mrp_production.state = 'done'
              AND stock_move.state = 'done'
              AND stock_move.product_id IN %s
              AND mrp_production.company_id = %s
        """
        mrp_params = [product_tuple, company_id]
        if from_datetime:
            mrp_query += " AND mrp_production.date_finished >= %s"
            mrp_params.append(from_datetime)
        if to_datetime:
            mrp_query += " AND mrp_production.date_finished <= %s"
            mrp_params.append(to_datetime)
        mrp_query += """
            GROUP BY mrp_production.product_id,
                     stock_move.product_id,
                     stock_move.uom_id
        """
        self.env.cr.execute(mrp_query, tuple(mrp_params))
        query_data = self.env.cr.dictfetchall()

        # Unbuild query with company filter
        un_build_dict = {}
        if self.un_build_orders:
            unbuild_query = """
                SELECT mrp_unbuild.product_id AS parent_product_id,
                       stock_move.product_id AS child_product_id,
                       SUM(COALESCE(stock_move.product_qty, stock_move.product_uom_qty, 0)) AS child_quantity_used
                FROM stock_move
                INNER JOIN mrp_unbuild ON stock_move.unbuild_id = mrp_unbuild.id
                WHERE stock_move.state = 'done'
                  AND stock_move.product_id IN %s
                  AND mrp_unbuild.company_id = %s
            """
            unbuild_params = [product_tuple, company_id]
            if from_datetime:
                unbuild_query += " AND mrp_unbuild.create_date >= %s"
                unbuild_params.append(from_datetime)
            if to_datetime:
                unbuild_query += " AND mrp_unbuild.create_date <= %s"
                unbuild_params.append(to_datetime)
            unbuild_query += """
                GROUP BY mrp_unbuild.product_id,
                         stock_move.product_id
            """
            self.env.cr.execute(unbuild_query, tuple(unbuild_params))
            for row in self.env.cr.dictfetchall():
                key = (row['parent_product_id'], row['child_product_id'])
                un_build_dict[key] = row.get('child_quantity_used') or 0.0

        # Pre-fetch products and UoMs in batches (avoids N+1 queries)
        parent_pids = {row['parent_product_id'] for row in query_data}
        child_pids = {row['child_product_id'] for row in query_data}
        uom_ids = {row['uom'] for row in query_data}

        products = {p.id: p.display_name for p in self.env[
            'product.product'].sudo().browse(parent_pids | child_pids)}
        uoms = {u.id: u.name for u in self.env[
            'uom.uom'].sudo().browse(uom_ids)}

        body = []
        heading = []
        for data in query_data:
            parent_id = data['parent_product_id']
            child_id = data['child_product_id']
            qty_used = data.get('child_product_used') or 0.0

            if self.un_build_orders:
                qty_used -= un_build_dict.get((parent_id, child_id), 0.0)

            # Include all positive fractional or integer quantities
            if qty_used > 0:
                child_name = products.get(child_id, '')
                product_dict = {
                    'parent_product_id': parent_id,
                    'parent_product_name': products.get(parent_id, ''),
                    'child_quantity_used': qty_used,
                    'uom': uoms.get(data['uom'], ''),
                    'child_product_name': child_name,
                    'child_product_id': child_id,
                }
                body.append(product_dict)
                head_dict = {'child_product_name': child_name}
                if head_dict not in heading:
                    heading.append(head_dict)

        if not body:
            raise ValidationError(self.env._("No data is available"))

        data = {
            'heading': heading,
            'body': body,
            'from_date': self.from_date,
            'to_date': self.to_date,
        }
        return self.env.ref(
            'bom_product_wise_usage_report.action_bom_usage_report'
        ).sudo().report_action(None, data=data, config=False)