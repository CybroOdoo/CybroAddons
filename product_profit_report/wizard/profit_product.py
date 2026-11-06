# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class ProfitProduct(models.TransientModel):
    """Transient model for wizard"""
    _name = "profit.product"
    _description = 'Product Profit'

    @api.model
    def _get_from_date(self):
        """This method returns first day in the year"""
        return self.env.company.compute_fiscalyear_dates(
            fields.Date.today())['date_from']

    from_date = fields.Date(
        required=True,
        default=lambda self: self._get_from_date(),
        help="Start date of the report period")
    to_date = fields.Date(default=fields.Date.context_today,
                          required=True,
                          help="End date of the report period")
    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda self: self.env.company.id,
        help="Select your company (shown only when multi-company is enabled)")
    categ_id = fields.Many2one('product.category', string='Product Category',
                               required=True,
                               help="Choose the product category")
    product_id = fields.Many2one('product.product',
                                 help="Select the product")
    product_product_ids = fields.Many2many(
        'product.product', string="Products",
        help="Products of the selected category, used as the domain "
             "of the Product field")

    def get_all_child_categories(self, category):
        """This function returns all child categories"""
        all_child_ids = category.child_id.ids
        for child_category in category.child_id:
            all_child_ids += self.get_all_child_categories(child_category)
        return all_child_ids

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        """Show products that correspond to the selected category"""
        self.product_id = False
        if self.categ_id:
            self.product_product_ids = [
                (6, 0, self.env['product.product'].search(
                    [('categ_id', 'in', [
                        self.categ_id.id] + self.get_all_child_categories(
                        self.categ_id))]).ids)]
        else:
            self.product_product_ids = [(5, 0, 0)]

    def action_print_pdf_report(self):
        """Print the pdf report"""
        report_action = self.env.ref(
            'product_profit_report.product_profit_report_action')
        return report_action.with_context(landscape=True).report_action(
            self, data={'form': self.read([])[0]})
