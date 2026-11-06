# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CommissionProduct(models.Model):
    """Commission.product model is defined here"""
    _name = 'commission.product'
    _description = 'Commission Product Wise'

    user_id = fields.Many2one('res.users',
                              help='Select the User')
    category_id = fields.Many2one('product.category',
                                  string='Product Category',
                                  help='Select the Product Category')
    category_ids = fields.Many2many('product.category',
                                    string='Product Category Reference',
                                    help="To set the domain for the "
                                         "category_id",
                                    compute="_compute_category_id")
    product_id = fields.Many2one('product.product',
                                 help='Select the product')
    commission_amount_type = fields.Selection([('percentage', 'Percentage'),
                                               ('fixed', 'Fixed Amount')],
                                              string="Amount Type",
                                              default='percentage',
                                              help='Commission amount type')
    fixed_amount = fields.Monetary('Commission Amount', default=0.0,
                                   help='Fixed Commission Amount')
    percentage = fields.Float(string='Rate in Percentage (%)',
                              help='Rate in percentage')
    amount = fields.Monetary('Maximum Commission Amount', default=0.0,
                             help='Maximum Commission Amount')
    currency_id = fields.Many2one("res.currency",
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id,
                                  help='Currency of the company')
    commission_id = fields.Many2one("crm.commission",
                                    help='Select The Crm Commission')

    @api.depends('category_id')
    def _compute_category_id(self):
        """Set the available category domain, including child categories."""
        for rec in self:
            rec.category_ids = rec._get_category_descendants()

    def _get_category_descendants(self):
        """Return the selected category and all of its child categories."""
        self.ensure_one()
        if not self.category_id:
            return self.env['product.category']
        return self.env['product.category'].search([
            ('id', 'child_of', self.category_id.id),
        ])

    @api.onchange('category_id')
    def _onchange_category_id(self):
        """Clear the product when it is outside the selected category tree."""
        for rec in self:
            categories = rec._get_category_descendants()
            if rec.product_id and rec.product_id.categ_id not in categories:
                rec.product_id = False

    @api.constrains('category_id', 'product_id')
    def _check_product_category(self):
        """Prevent invalid product-category combinations outside the UI."""
        for rec in self:
            if (rec.category_id and rec.product_id
                    and rec.product_id.categ_id not in
                    rec._get_category_descendants()):
                raise ValidationError(self.env._(
                    "The selected product must belong to the selected "
                    "product category or one of its child categories."
                ))
