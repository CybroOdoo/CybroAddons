# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """ This class inherits 'res.config.settings' and adds fields """
    _inherit = 'res.config.settings'

    require_standard_price = fields.Boolean(
        string='Standard Price as a Code',
        config_parameter='customized_barcode_generator.require_standard_price',
        help="Show the product cost on product labels as a code.")
    require_ref = fields.Boolean(
        string='Show Product Reference',
        config_parameter='customized_barcode_generator.require_ref',
        help="Show the product reference next to the cost code on product "
             "labels.")
