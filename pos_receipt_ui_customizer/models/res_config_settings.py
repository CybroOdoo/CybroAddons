# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Neeraj JR (<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    """
    Adds POS options for enabling custom receipts and selecting a receipt design.
    """
    _inherit = 'res.config.settings'

    is_custom_receipt = fields.Boolean(string='Is Custom Receipt', related='pos_config_id.is_custom_receipt',
                                       readonly=False,
                                       help='Indicates the receipt  design is '
                                            'custom or not')
    receipt_design_id = fields.Many2one('pos.receipt', string='Receipt Design',
                                        related='pos_config_id.receipt_design_id',
                                        readonly=False, help='Choose any receipt design')