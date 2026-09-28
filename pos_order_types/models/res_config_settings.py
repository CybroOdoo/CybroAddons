# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jigin K (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """To insert field in settings"""
    _inherit = 'res.config.settings'

    pos_is_order_type = fields.Boolean(string='Order Type',
                                       related="pos_config_id.is_order_type",
                                       readonly=False,
                                       help="Enable order type feature in POS settings."
                                       )
    pos_order_type_ids = fields.Many2many(
        related="pos_config_id.order_type_ids",
        readonly=False,
        help="Configure order types for the POS."
    )

    @api.onchange('pos_is_order_type')
    def _onchange_pos_is_order_type(self):
        """To clear order_type_ids field in the pos.config
        the while disable the is_order_type in pos.config"""
        if not self.pos_is_order_type:
            self.pos_order_type_ids = False
