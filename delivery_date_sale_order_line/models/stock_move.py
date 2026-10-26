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
from odoo.fields import Domain


class StockMove(models.Model):
    """Inheriting stock move to add delivery date and handle picking grouping."""
    _inherit = 'stock.move'

    delivery_datetime = fields.Datetime(
        string='Expected Delivery Date',
        help='Delivery date for the product',
    )

    def _get_new_picking_values(self):
        """Pass delivery_datetime to new picking values and update scheduled_date
        only if delivery_datetime is provided on outgoing pickings.
        """
        res = super()._get_new_picking_values()
        delivery_datetime = self[0].delivery_datetime if self else False
        res['delivery_datetime'] = delivery_datetime
        picking_type = self[0].picking_type_id if self else False
        if picking_type and picking_type.code == 'outgoing' and delivery_datetime:
            res['scheduled_date'] = delivery_datetime
        return res

    def _key_assign_picking(self):
        """Group moves by delivery date so moves with different delivery dates
        are split into distinct pickings.
        """
        keys = super()._key_assign_picking()
        return keys + (self.delivery_datetime,)

    def _search_picking_for_assignation_domain(self):
        """Extend picking search domain to match on delivery_datetime."""
        domain = super()._search_picking_for_assignation_domain()
        if self.delivery_datetime:
            domain = Domain.AND([domain, [('delivery_datetime', '=', self.delivery_datetime)]])
        else:
            domain = Domain.AND([domain, [('delivery_datetime', '=', False)]])
        return domain
