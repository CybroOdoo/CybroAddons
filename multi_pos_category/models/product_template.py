# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models, api


class ProductTemplate(models.Model):
    """This model was inherited for replace existing field pos_categ_id."""
    _inherit = 'product.template'

    pos_categ_ids = fields.Many2many('pos.category', string="Pos Categories",
                                     help="Categories used in the Point of Sale.")

    # Keep the original field for compatibility with Odoo's built-in features
    # BUT we need to handle it differently for multi-category support
    pos_categ_id = fields.Many2one('pos.category', string="Main Pos Category",
                                   compute='_compute_main_pos_category',
                                   store=True,
                                   help="Main category used for filtering (first category in pos_categ_ids)")

    @api.depends('pos_categ_ids')
    def _compute_main_pos_category(self):
        """Set the first category as main category for compatibility"""
        for product in self:
            product.pos_categ_id = product.pos_categ_ids[
                                   :1] if product.pos_categ_ids else False