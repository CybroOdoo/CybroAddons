# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherits 'res.config.settings' and adds new fields """
    _inherit = 'res.config.settings'

    is_custom_invoice = fields.Boolean(string='Custom Invoice',
                                       config_parameter='invoice_design.is_custom_invoice',
                                       help="Enable to print custom invoice")
    invoice_design_id = fields.Many2one('invoice.design',
                                        string='Invoice Design',
                                        config_parameter='invoice_design.invoice_design',
                                        help="Choose your custom design")
    invoice_template = fields.Text(related='invoice_design_id.invoice_template',
                                   string='Receipt XML',
                                   help='Template of the invoice design chosen')
