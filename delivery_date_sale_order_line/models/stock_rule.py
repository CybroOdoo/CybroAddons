#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models


class StockRule(models.Model):
    """Inheriting stock rule to propagate delivery_datetime to moves."""
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        """Propagate delivery_datetime from procurement values to created stock moves."""
        fields = super()._get_custom_move_fields()
        fields.append('delivery_datetime')
        return fields
