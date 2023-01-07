# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Afra K (<https://www.cybrosys.com>)
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
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_receipt_design = fields.Many2one(related='pos_config_id.receipt_design', string="Receipt Design",
                                         help="Choose any receipt design", compute='_compute_pos_is_custom_receipt',
                                         readonly=False, store=True)
    pos_design_receipt = fields.Text(related='pos_config_id.design_receipt', string='Receipt XML')
    pos_is_custom_receipt = fields.Boolean(related='pos_config_id.is_custom_receipt', readonly=False, store=True)

    @api.depends('pos_is_custom_receipt', 'pos_config_id')
    def _compute_pos_is_custom_receipt(self):
        for res_config in self:
            if res_config.pos_is_custom_receipt:
                res_config.pos_receipt_design = res_config.pos_config_id.receipt_design
            else:
                res_config.pos_receipt_design = False
