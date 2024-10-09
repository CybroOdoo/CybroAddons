# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha MK (odoo@cybrosys.com)
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
from odoo import fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """ResConfigSettings class for adding the limit and status of products"""
    _inherit = 'res.config.settings'

    limit = fields.Integer(string='Limit', default=0,
                           config_parameter='purchase_product_history.limit',
                           help='Specify the limit to show')
    status = fields.Selection(
        [('all', 'All'), ('rfq', 'RFQ'), ('purchase_order', 'Purchase Order')],
        string='Status',
        config_parameter='purchase_product_history.status',
        help='Specify the status of the purchase order')

    def set_values(self):
        """inorder to set values in the settings"""
        res = super().set_values()
        self.env['ir.config_parameter'].set_param(
            'purchase_product_history.limit',
            self.limit)
        self.env['ir.config_parameter'].set_param(
            'purchase_product_history.status',
            self.status)
        if self.limit < 0:
            raise ValidationError("Limit cannot be less than 0")
        return res
