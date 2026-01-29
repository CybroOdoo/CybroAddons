# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    """add field in pos config to select custom receipts"""

    receipt_design_id = fields.Many2one('pos.receipt', string="Receipt Design",
                                        help="Choose any receipt design")
    design_receipt = fields.Text(related='receipt_design_id.design_receipt',
                                 string='Receipt XML',
                                 help="Helps to get related receipt design")
    is_custom_receipt = fields.Boolean(string='Is Custom Receipt',
                                       help="Boolean field to enable the "
                                            "custom receipt design")
