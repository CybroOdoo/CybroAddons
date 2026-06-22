# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
        for line in self:
            fleet_model = line.move_id.fleet_rent_id
            if fleet_model and line.move_id.is_first_invoice:
                fleet_model.first_payment = line.price_unit
