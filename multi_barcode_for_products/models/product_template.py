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


class ProductTemplate(models.Model):
    """
    Model for managing product templates.

    Inherits:
        product.template (product.template): The default Odoo product template
        model.
        """

    _inherit = 'product.template'

    template_multi_barcodes_ids = fields.One2many('product.multiple.barcodes',
                                                  'template_barcode_id',
                                                  string='Barcodes',
                                                  help='Set multiple'
                                                       ' barcodes for this '
                                                       'product template')

    def write(self, vals):
        """
        Overrides the write method of the Odoo model.

        Args:
            vals (dict): A dictionary of field names and their new values to
            write to the record.

        Returns:
            object: A reference to the updated record.

        """
        res = super(ProductTemplate, self).write(vals)
        if self.template_multi_barcodes_ids:
            self.template_multi_barcodes_ids.update({
                'product_barcode_id': self.product_variant_id.id
            })
        return res

    @api.model
    def create(self, vals):
        """
        Overrides the create method of the Odoo model.

        Args:
            vals (dict): A dictionary of field names and their values to create
             the new record with.

        Returns:
            object: A reference to the newly created record.

        """
        res = super(ProductTemplate, self).create(vals)
        res.template_multi_barcodes_ids.update({
            'product_barcode_id ': res.product_variant_id.id
        })
        return res
