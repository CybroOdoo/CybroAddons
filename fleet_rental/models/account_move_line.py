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
from odoo import api, models


class AccountMoveLine(models.Model):
    """Inherit account.move.line"""
    _inherit = 'account.move.line'

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        """
            Update the 'first_payment' field of the associated
            'car.rental.contract' model when the 'price_unit' field changes.
        """
        fleet_model = self.move_id.fleet_rent_id
        if fleet_model:
            fleet_model.first_payment = self.price_unit
