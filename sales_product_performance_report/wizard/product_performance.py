# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sabeel B (odoo@cybrosys.com)
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
from itertools import zip_longest
from odoo import fields, models, tools, _
from odoo.exceptions import UserError
from odoo.http import request


class ProductPerformance(models.TransientModel):
    _name = 'product.performance'
    _description = "Product Performance Reports"

    @tools.ormcache()
    def _get_default_category_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('product.product_category_all')

    start_date = fields.Date(string="Start Date", help="The start date")
    end_date = fields.Date(string="End Date", help="The end date")
    up_to_date_report = fields.Boolean(string="Report Up To Date",
                                       help='for get up to date report')
    product_ids = fields.Many2many('product.template',
                                   string='Product',
                                   help='for get product',
                                   domain="[('categ_id', 'child_of', "
                                          "categ_id)]")
    categ_id = fields.Many2one('product.category',
                               string='Product Category',
                               help='Product Categories',
                               default=_get_default_category_id,
                               required=True)
    company_ids = fields.Many2many('res.company', string='Company',
                                  help='Res Company')

    def product_performance(self):
        """
           return: to sale order tree view and form view
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
                raise UserError(_("No products in this Company!"))
        tree_view_id = request.env.ref(
            'sales_product_performance_report.'
            'view_product_template_report_tree').id
        domain = [('id', 'in', products) if products else None]
        if companies:
            domain.append(('company_id', 'in', companies))
        return {
            'name': _('Product Performance Report'),
            'res_model': 'product.template',
            'views': [(tree_view_id, 'list')],
            'view_id': tree_view_id,
            'type': 'ir.actions.act_window',
            'target': 'fullscree',
            'domain': domain if products else None,
            'context': {
                'create': False,
                'start_date': self.start_date if self.start_date else None,
                'end_date': self.end_date if self.end_date else None,
                'up_to_date': self.up_to_date_report
            }
        }
