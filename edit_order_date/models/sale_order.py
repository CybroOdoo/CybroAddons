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
from odoo import fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Inherit Sale Order to restrict date_order editing to authorized users."""

    _inherit = 'sale.order'

    def write(self, values):
        """Restrict modifying 'date_order' on confirmed orders for users without access."""
        if 'date_order' in values and not self.env.user.has_group(
            'edit_order_date.edit_order_date_group_user',
        ):
            new_date = fields.Datetime.to_datetime(values['date_order'])
            for order in self:
                if order.state == 'sale' and order.date_order != new_date:
                    raise UserError(self.env._("You have no access to change 'Order Date'"))
        return super().write(values)
