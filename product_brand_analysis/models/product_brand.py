# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields


class ProductBrand(models.Model):
    _name = "product.brand"
    _rec_name = 'brand_name'

    brand_name = fields.Char('Brand Name', required=True)
    product_templates = fields.One2many('product.template', 'brand_details', string='Products')


class ProductTemplate(models.Model):
    _inherit = "product.template"

    brand_details = fields.Many2one('product.brand', string='Brand')


class SaleReport(models.Model):
    _inherit = "sale.report"

    brand_details = fields.Many2one('product.brand', string="Brand", readonly=True)

    def _select(self):
        return super(SaleReport, self)._select() + ", t.brand_details as brand_details"

    def _group_by(self):
        return super(SaleReport, self)._group_by() + ", t.brand_details"


