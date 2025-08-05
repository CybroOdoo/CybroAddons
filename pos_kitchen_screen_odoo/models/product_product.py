from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


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