# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Dhanya B(<https://www.cybrosys.com>)
#
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class QualityMeasure(models.Model):
    _name = 'quality.measure'
    _description = 'Quality Measure'
    _inherit = ['mail.thread']
    _order = "id desc"

    name = fields.Char('Name', required=True)
    product_id = fields.Many2one('product.product', string='Product',
                                 index=True, ondelete='cascade',
                                 track_visibility='onchange')
    product_template_id = fields.Many2one('product.template',
                                          string='Product Template',
                                          related='product_id.product_tmpl_id')
    type = fields.Selection(
        [('quantity', 'Quantitative'),
         ('quality', 'Qualitative')],
        string='Test Type', default='quantity', required=True,
        track_visibility='onchange')
    quantity_min = fields.Float('Min-Value', track_visibility='onchange')
    quantity_max = fields.Float('Max-Value', track_visibility='onchange')
    picking_type_ids = fields.Many2many('stock.picking.type',
                                        string='Trigger On')
    active = fields.Boolean('Active', default=True,
                            track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda
                                     self: self.env.user.company_id.id, index=1)

    @api.onchange('type')
    def onchange_type(self):
        """Handles the onchange event for the `type` field."""
        if self.type == 'quality':
            self.quantity_min = 0.0
            self.quantity_max = 0.0
