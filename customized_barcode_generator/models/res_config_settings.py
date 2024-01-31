# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana haseen(<https://www.cybrosys.com>)
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


class ResConfigSettings(models.TransientModel):
    """This class inherits 'res.config.settings' and adds fields"""
    _inherit = 'res.config.settings'

    require_standard_price = fields.Boolean(string='Standard price as a code',
                                            config_parameter='customized_barcode_generator.require_standard_price',
                                            help="check this box to show "
                                                 "cost on the product labels "
                                                 "as code.")
    require_ref = fields.Boolean(string='Show product reference ',
                                 config_parameter='customized_barcode_generator.require_ref',
                                 help="check this box to show product reference"
                                      "as in product labels.")
