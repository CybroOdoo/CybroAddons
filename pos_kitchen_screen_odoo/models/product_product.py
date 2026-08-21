# -*- coding: utf-8 -*-
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
############################################################################
from odoo import models, fields, api
from odoo.exceptions import ValidationError



class ProductProduct(models.Model):
    _inherit = 'product.product'

    prepair_time_minutes = fields.Float(
        string='Preparation Time (MM:SS)',
        digits=(12, 2),
        help="Enter time in MM:SS format (e.g., 20:12 for 20 minutes 12 seconds)"
    )

    @api.onchange('prepair_time_minutes')
    def _onchange_prepair_time(self):
        if isinstance(self.prepair_time_minutes, str):
            try:
                # Validate format MM:SS
                if not re.match(r'^\d{1,3}:[0-5][0-9]$', self.prepair_time_minutes):
                    raise ValidationError("Please enter time in MM:SS format (e.g., 20:12)")

                minutes, seconds = map(int, self.prepair_time_minutes.split(':'))
                self.prepair_time_minutes = minutes + (seconds / 60.0)
            except (ValueError, AttributeError):
                raise ValidationError("Invalid time format. Please use MM:SS (e.g., 20:12)")