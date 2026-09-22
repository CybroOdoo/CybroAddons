# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ashwin T (odoo@cybrosys.com)
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
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ForecastAnalysisReport(models.TransientModel):
    """Class to handle forecast analysis report"""
    _name = 'forecast.analysis.report'
    _description = 'Forecast Analysis Report'

    parent_category_id = fields.Many2one(
        'product.category', string="Parent Category",
        help="Parent category of product")
    product_category_id = fields.Many2one(
        'product.category', string="Product Category",
        help="Category of the product",
        domain="[('parent_id','=',parent_category_id)]")
    partner_id = fields.Many2one('res.partner', string="Supplier",
                                 help="Related Partner.")
    product_brand_id = fields.Many2one('product.brand',
                                       string="Product Brand",
                                       help="Brand of the Product.")
    period = fields.Selection([('1week', 'Last 1 week'),
                               ('2week', 'Last 2 weeks'),
                               ('3week', 'Last 3 weeks'),
                               ('1month', 'Last 1 month'),
                               ('2months', 'Last 2 months'),
                               ('3months', 'Last 3 months'),
                               ('6months', 'Last 6 months'),
                               ('12months', 'Last 12 months'),
                               ('24months', 'Last 24 months'),
                               ('36months', 'Last 36 months'),
                               ], string='Duration', required=True,
                              default='3months',
                              help="The duration of the report. 3 months is "
                                   "the default duration")
    location_ids = fields.Many2many('stock.location',
                                    string="Locations",
                                    help="Product locations.")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company,
                                 string="Company",
                                 help="Company of the Product belongs to.")

    def get_start_date(self, today):
        """This function will calculate the start_date with respect to the
        period and returns the result"""
        res = fields.Date.subtract(today, months=3)
        if self.period == '1week':
            res = fields.Date.subtract(today, weeks=1)
        elif self.period == '2week':
            res = fields.Date.subtract(today, weeks=2)
        elif self.period == '3week':
            res = fields.Date.subtract(today, weeks=3)
        elif self.period == '1month':
            res = fields.Date.subtract(today, months=1)
        elif self.period == '6months':
            res = fields.Date.subtract(today, months=6)
        elif self.period == '12months':
            res = fields.Date.subtract(today, months=12)
        elif self.period == '24months':
            res = fields.Date.subtract(today, months=24)
        elif self.period == '36months':
            res = fields.Date.subtract(today, months=36)
        elif self.period == '2months':
            res = fields.Date.subtract(today, months=2)
        return res

    def action_print_report(self):
        """This function will generate the report based on the values
        on the report wizard and returns the report."""
        previous_report = self.env['forecast.report'].search([])
        previous_report.unlink() if previous_report else False
        if (not self.product_category_id and not self.parent_category_id and
                not self.partner_id and not self.product_brand_id and
                not self.location_ids):
            raise ValidationError(_("Data missing"))
        domain = [('is_storable', '=', True)]
        if self.parent_category_id and self.product_category_id:
            domain += [('categ_id', '=', self.product_category_id.id)]
        elif not self.product_category_id and self.parent_category_id:
            domain += [('categ_id', '=', self.parent_category_id.id)]
        if self.partner_id:
            suppliers = self.env['product.supplierinfo'].search(
                [('partner_id', '=', self.partner_id.id)])
            domain += [('seller_ids', 'in', suppliers.ids)]
        if self.product_brand_id:
            domain += [('product_brand_id', '=', self.product_brand_id.id)]
        products = self.env['product.product'].search(domain)
        product_ids = tuple([product.id for product in products])
        current_date = fields.Date.today()
        start_date = self.get_start_date(current_date)
        query = """
               SELECT sl.product_id,
                      so.warehouse_id,
                      sum(sl.qty_invoiced) AS qty_invoiced
               FROM sale_order_line AS sl
               JOIN sale_order AS so ON sl.order_id = so.id
               WHERE so.state IN ('sale','done')
               AND so.date_order::date >= %s
               AND so.date_order::date <= %s
               AND sl.product_id in %s 
               GROUP BY sl.product_id, so.warehouse_id"""
        params = start_date, current_date, \
            product_ids if product_ids else (0, 0, 0, 0)
        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        sales_map = {}
        for sol in result:
            sales_map[(sol['product_id'], sol['warehouse_id'])] = sol['qty_invoiced'] or 0.0
        internal_locations = self.env['stock.location'].search(
            [('usage', '=', 'internal')])
        for product in products:
            if self.location_ids:
                locations = self.location_ids
            else:
                quant_locs = self.env['stock.quant'].search([
                    ('product_id', '=', product.id),
                    ('location_id', 'in', internal_locations.ids)]).mapped('location_id')
                orderpoint_locs = self.env['stock.warehouse.orderpoint'].search([
                    ('product_id', '=', product.id),
                    ('location_id', 'in', internal_locations.ids)]).mapped('location_id')
                locations = quant_locs | orderpoint_locs
            for location in locations:
                stock_quant = self.env['stock.quant'].search([
                    ('location_id', '=', location.id),
                    ('product_id', '=', product.id)])
                available_qty = sum(quant.quantity for quant in stock_quant)
                sold = sales_map.get((product.id, location.warehouse_id.id), 0.0) if location.warehouse_id else 0.0
                forecasted_qty = product.with_context(
                    location=location.id).virtual_available
                reorder_qty = self.env['stock.warehouse.orderpoint'].search([
                    ('product_id', '=', product.id),
                    ('location_id', '=', location.id)])
                reorder_min = sum(qty.product_min_qty for qty in reorder_qty)
                minimum_qty = reorder_min if available_qty < reorder_min else 0
                pending = product.with_context(
                    from_date=start_date, to_date=current_date,
                    location=location.id).incoming_qty

                suggested = max(0.0, (sold + minimum_qty) - (available_qty + pending))

                if not (available_qty or forecasted_qty or pending or sold or minimum_qty):
                    continue

                if self.partner_id:
                    supplier = product.seller_ids.filtered(
                        lambda seller: seller.partner_id == self.partner_id
                    )[:1].id
                elif not self.partner_id and product.seller_ids:
                    supplier = product.seller_ids.ids[0]
                else:
                    supplier = False

                vals = {
                    'sold': sold,
                    'product_id': product.id,
                    'product_category_id': product.categ_id.id,
                    'supplier_id': supplier,
                    'product_brand_id': product.product_brand_id.id,
                    'on_hand': available_qty,
                    'pending': pending,
                    'minimum': minimum_qty,
                    'suggested': suggested,
                    'forecast': forecasted_qty,
                    'location_id': location.id
                }
                self.env['forecast.report'].create(vals)
        return {
            'name': _('Forecast Analysis Report'),
            'res_model': 'forecast.report',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,pivot,form',
            'views': [(self.env.ref('inventory_forecast_analysis_report.'
                                    'forecast_report_view_tree'
                                    ).id, 'list'),
                      (self.env.ref('inventory_forecast_analysis_report.'
                                    'forecast_report_view_pivot').id,
                       'pivot'),
                      (False, 'form')],
            'target': 'current',
        }
