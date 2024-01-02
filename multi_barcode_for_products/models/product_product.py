# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    """
    This class inherits the `product.product`model and adds the functionality to
    set multiple barcodes for a product.

    """

    _inherit = 'product.product'

    multi_barcodes_ids = fields.One2many('product.multiple.barcodes',
                                         'product_barcode_id', string='Barcodes',
                                         help='Set multiple barcode')

    def _check_multi_barcode(self, domain):
        """
        Private method that checks if the product has multiple barcodes and
        returns the product id.

        Args:
            domain (list): A list of tuples containing the search criteria.

        Returns:
            int or None: The ID of the product if multiple barcodes are found,
            None otherwise.
        """
        product_id = None
        if len(domain) > 1:
            if 'barcode' in domain[0]:
                barcode = domain[0][2]
                product_multi_barcode = self.env['product.multiple.barcodes'].search(
                    [('product_multi_barcode', '=', barcode)])
                if product_multi_barcode:
                    product_id = product_multi_barcode.product_barcode_id.id
        return product_id

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None,
                    order=None):
        """
        This method overrides the `search_read` method of the `product.product`
        model to search for products with alternate barcodes.

        Args:
            domain (list): A list of tuples containing the search criteria.
            fields (list): A list of fields to include in the search results.
            offset (int): The starting index of the search results.
            limit (int): The maximum number of search results to return.
            order (str): The order in which to return the search results.

        Returns:
            list: A list of dictionaries representing the search results.
        """
        product_id = self._check_multi_barcode(domain)
        if product_id:
            domain = [('id', '=', product_id)]

        res = super().search_read(domain=domain, fields=fields, offset=offset,
                                  limit=limit, order=order)
        return res

    @api.model
    def create(self, vals):
        """
        This method overrides the `create` method of the `product.product`
        model to add the product template ID to the alternate barcodes.

        Args:
            vals (dict): A dictionary containing the values to create the
             product with.

        Returns:
            product.product: The created product.
        """
        res = super(ProductProduct, self).create(vals)
        res.multi_barcodes_ids.update({
            'template_barcode_id': res.product_tmpl_id.id
        })
        return res

    def write(self, vals):
        """
        This method overrides the `write` method of the `product.product` model
        to update the product template ID in the alternate barcodes.

        Args:
            vals (dict): A dictionary containing the values to update the
            product with.

        Returns:
            bool: True if the write operation is successful, False otherwise.
        """
        res = super(ProductProduct, self).write(vals)
        if self.multi_barcodes_ids:
            self.multi_barcodes_ids.update({
                'template_barcode_id': self.product_tmpl_id.id
            })
        return res
