# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjali VP (Contact : odoo@cybrosys.com)
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
#############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosMultiUom(models.Model):
    _name = 'pos.multi.uom'
    _inherit = ['pos.load.mixin']
    _description = 'POS Multiple Unit of Measure'
    _rec_name = 'uom_id'

    product_template_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True,
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True,
        ondelete='restrict',
    )

    factor = fields.Float(
        string='Conversion Factor',
        default=1.0,
        required=True,
        digits=(12, 6),
    )

    price = fields.Float(
        string='POS Price',
        digits='Product Price',
    )

    _unique_product_uom = models.Constraint(
        'unique(product_template_id, uom_id)',
        'Each UoM can only be defined once per product!'
    )

    @api.constrains('factor')
    def _check_factor(self):
        """Constraint to check if the factor is greater than zero."""
        for record in self:
            if record.factor <= 0:
                raise ValidationError(_('Factor must be greater than zero.'))

    @api.model
    def _load_pos_data_domain(self, data, config):
        """Returns the domain for loading pos.multi.uom data."""
        return []

    @api.model
    def _load_pos_data_fields(self, config):
        """Returns the fields for loading pos.multi.uom data."""
        return ['id', 'product_template_id', 'uom_id', 'factor', 'price']
