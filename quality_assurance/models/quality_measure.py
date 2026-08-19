# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models


class QualityMeasure(models.Model):
    """Quality rules used to generate quality tests."""
    _name = 'quality.measure'
    _description = 'Quality Measure'
    _inherit = ['mail.thread']
    _order = "id desc"

    name = fields.Char('Name', required=True)
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        index=True,
        ondelete='cascade',
        tracking=True
    )
    product_template_id = fields.Many2one(
        'product.template',
        string='Product Template',
        related='product_id.product_tmpl_id'
    )
    type = fields.Selection(
        [('quantity', 'Quantitative'),
         ('quality', 'Qualitative')],
        string='Test Type',
        default='quantity',
        required=True,
        tracking=True
    )
    quantity_min = fields.Float(
        'Min-Value',
        tracking=True
    )
    quantity_max = fields.Float(
        'Max-Value',
        tracking=True
    )
    picking_type_ids = fields.Many2many(
        'stock.picking.type',
        string='Trigger On'
    )
    active = fields.Boolean(
        'Active',
        default=True,
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id.id,
        index=1
    )

    @api.onchange('type')
    def onchange_type(self):
        """Reset quantity limits for qualitative tests."""
        if self.type == 'quality':
            self.quantity_min = 0.0
            self.quantity_max = 0.0
