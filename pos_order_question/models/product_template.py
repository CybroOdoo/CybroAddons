# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
from odoo import fields, models, api


class ProductTemplate(models.Model):
    """Inherited model product_template to add a new field"""
    _inherit = 'product.template'

    order_question_ids = fields.One2many(
        'pos.order.question',
        'product_tmpl_id',
        string='Order Questions',
        help="Questions of the template"
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Extend the POS data fields list."""
        res = super()._load_pos_data_fields(config_id)
        res.append('order_question_ids')
        return res
