# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from itertools import zip_longest
from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from odoo.http import request


class ProductPerformance(models.TransientModel):
    """Wizard model for generating product performance reports."""
    _name = 'product.performance'
    _description = "Product Performance Reports"

    @tools.ormcache()
    def _get_default_category_id(self):
        """Get a default category - returns the first root category or False"""
        # Try to find the first root level category (parent_id is False)
        root_category = self.env['product.category'].search(
            [('parent_id', '=', False)], limit=1
        )
        return root_category.id if root_category else False

    start_date = fields.Date(
        string="Start Date",
        help="The start date"
    )
    end_date = fields.Date(
        string="End Date",
        help="The end date"
    )
    up_to_date_report = fields.Boolean(
        string="Report Up To Date",
        help='for get up to date report'
    )
    product_ids = fields.Many2many(
        comodel_name='product.template',
        string='Product',
        help='for get product',
        domain="[('categ_id', 'child_of', "
               "categ_id)]"
    )
    categ_id = fields.Many2one(
        comodel_name='product.category',
        string='Product Category',
        help='Product Categories',
        default=_get_default_category_id,
        required=True
    )
    company_ids = fields.Many2many(
        comodel_name='res.company',
        string='Company',
        help='Res Company'
    )

    @api.constrains('start_date', 'end_date')
    def _check_date_validation(self):
        """Ensure the end date is not earlier than the start date."""
        for record in self:
            if record.start_date and record.end_date:
                if record.end_date < record.start_date:
                    raise UserError(
                        "End Date must be greater than or equal to Start Date.")

    def product_performance(self):
        """
           return: to sale order list view and form view
        """
        products = []
        companies = []
        if self.product_ids:
            for product, company in zip_longest(self.product_ids,
                                                self.company_ids,
                                                fillvalue=None):
                products.append(product.id) if self.product_ids else None
                companies.append(company.id) if self.company_ids else None
                if product:
                    product.performance_values(self.start_date, self.end_date,
                                               self.up_to_date_report)
        else:
            if self.company_ids:
                product = self.env['product.template'].search(
                    [('categ_id', 'child_of', self.categ_id.id),
                     ('company_id', 'in', self.company_ids.ids)])
            else:
                product = self.env['product.template'].search(
                    [('categ_id', 'child_of', self.categ_id.id)])
            for rec in product:
                self.env['product.template'].browse(rec.id).performance_values(
                    self.start_date, self.end_date, self.up_to_date_report)
            if product:
                products = [each_product.id for each_product in product]
            else:
                raise UserError("No products in this Company!")
        list_view_id = request.env.ref(
            'sales_product_performance_report.view_product_template_report_list').id
        domain = [('id', 'in', products) if products else None]
        if companies:
            domain.append(('company_id', 'in', companies))
        return {
            'name': 'Product Performance Report',
            'res_model': 'product.template',
            'views': [(list_view_id, 'list')],
            'view_id': list_view_id,
            'type': 'ir.actions.act_window',
            'target': 'fullscreen',
            'domain': domain if products else None,
            'context': {
                'create': False,
                'start_date': self.start_date if self.start_date else None,
                'end_date': self.end_date if self.end_date else None,
                'up_to_date': self.up_to_date_report
            }
        }
