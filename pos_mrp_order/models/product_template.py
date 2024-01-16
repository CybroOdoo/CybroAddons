# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    you can modify it under the terms of the GNU AFFERO
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
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """ Inheriting 'product.template' for adding custom field and functionality.
    """
    _inherit = 'product.template'

    to_make_mrp = fields.Boolean(
        string='To Create MRP Order',
        help="Check if the product should make mrp order")

    @api.onchange('to_make_mrp')
    def onchange_to_make_mrp(self):
        """ Raise validation error if bom is not set in 'product.template'."""
        if self.to_make_mrp:
            if not self.bom_count:
                raise ValidationError(_(
                    'Please set Bill of Material for this product.'))
