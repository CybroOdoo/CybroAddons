# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jumana Jabin MP(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, models


class SerialNoValidation(models.Model):
    """Serial Number Validation Model.This model is used for serial number
       validation in Odoo."""
    _name = 'serial_no.validation'

    @api.model
    def validate_lots(self, lots):
        """ This method validates a list of lots."""
        processed = []
        LotObj = self.env['stock.lot']
        for lot in lots:
            lot_id = LotObj.search([('name', '=', lot)], limit=1)
            if lot_id.product_qty > 0 and lot not in processed:
                processed.append(lot)
                continue
            if lot in processed:
                return ['duplicate', lot]
            return ['no_stock', lot]
        return True
