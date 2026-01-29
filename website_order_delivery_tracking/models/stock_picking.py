# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    """ Add a field named 'tracking_status' in stock.picking to have the status
    of the delivery """
    _inherit = 'stock.picking'

    tracking_status = fields.Text(string='Tracking Status',
                                  help="Status of the picking")

    @api.constrains('carrier_tracking_ref')
    def _check_carrier_tracking_ref(self):
        """ To ensure tracking reference is not duplicated """
        duplicate_tracking_ref = self.search([
            ('carrier_tracking_ref', '=', self.carrier_tracking_ref)])
        for rec in self:
            ref = rec.carrier_tracking_ref
            if ref:
                if len(duplicate_tracking_ref) > 1:
                    raise ValidationError(_(
                        "This tracking reference already exists."))
