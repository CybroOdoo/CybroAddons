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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    """Inheriting sale order line to add delivery date."""
    _inherit = 'sale.order.line'

    delivery_datetime = fields.Datetime(
        string='Expected Delivery Date',
        help='Delivery date for the product',
    )

    @api.constrains('delivery_datetime')
    def _check_delivery_datetime(self):
        """Ensure the delivery date is today or in the future."""
        for line in self:
            if line.delivery_datetime and line.delivery_datetime.date() < fields.Date.context_today(line):
                raise ValidationError(_("The delivery date must be today or in the future."))

    def _prepare_procurement_values(self):
        """Prepare specific key for moves or other components that will be
        created from a stock rule coming from a sale order line.
        """
        res = super()._prepare_procurement_values()
        res['delivery_datetime'] = self.delivery_datetime
        if self.delivery_datetime:
            res['date_planned'] = self.delivery_datetime
        return res
