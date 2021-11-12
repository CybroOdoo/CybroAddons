# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
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
###################################################################################

from odoo import models, api, fields, _


class ProductPublishWizard(models.TransientModel):
    _name = 'product.publish.wizard'
    _description = "Product Publish/Unpublish"

    def product_multi_publish(self):
        active_ids = self._context.get('active_ids')
        products = self.env['product.template'].browse(active_ids)
        products = products.filtered(lambda product: product.sale_ok == True)
        for product in products:
            product.is_published = True

    def product__multi_unpublish(self):
        active_ids = self._context.get('active_ids')
        products = self.env['product.template'].browse(active_ids)
        products = products.filtered(lambda product: product.sale_ok == True)
        for product in products:
            product.is_published = False
