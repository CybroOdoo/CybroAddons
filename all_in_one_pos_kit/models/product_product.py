# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
from odoo.osv import expression


class ProductProduct(models.Model):
    """
    Inherit poduct_product model
    """
    _inherit = 'product.product'

    product_multi_barcodes = fields.One2many(
        comodel_name='multi.barcode.product',
        inverse_name='product_multi', string='Barcodes'
    )

    @api.model
    def create(self, vals):
        """
        Create a new product and update the associated multi barcodes record.

        Args:
            vals (dict): The values to create the product.

        Returns:
            recordset: The created product record.
        """
        res = super(ProductProduct, self).create(vals)
        res.product_multi_barcodes.update({
            'template_multi': res.product_tmpl_id.id
        })
        return res

    def write(self, vals):
        """
        Update the product and its associated multi barcodes record.

        Args:
            vals (dict): The values to update the product.

        Returns:
            bool: True if the update was successful.
        """
        res = super(ProductProduct, self).write(vals)
        self.product_multi_barcodes.update({
            'template_multi': self.product_tmpl_id.id
        })
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100,
                     name_get_uid=None):
        """
        Custom name search for products based on various fields.

        Args:
            name (str): The name to search for.
            args (list): Additional search criteria.
            operator (str): The operator for the search (default is 'ilike').
            limit (int): The maximum number of records to return.
            name_get_uid (int): The UID for access rights.

        Returns:
            list: List of product IDs that match the search criteria.
        """
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', operator, name),
                      ('default_code', operator, name),
                      '|', ('barcode', operator, name),
                      ('product_multi_barcodes', operator, name)]
        product_id = self._search(expression.AND([domain, args]), limit=limit,
                                  access_rights_uid=name_get_uid)
        return product_id

    @api.onchange('to_make_mrp')
    def onchange_to_make_mrp(self):
        """
        Triggered when the `to_make_mrp` field is changed.

        If the `to_make_mrp` field is set to True, this method checks if the
        product has an associated Bill of Materials (BoM). If no BoM is found,
        it raises a warning prompting the user to set a BoM for the product.

        Raises:
            Warning: If `to_make_mrp` is True and `bom_count` is 0.
        """
        if self.to_make_mrp:
            if not self.bom_count:
                raise Warning('Please set Bill of Material for this product.')
