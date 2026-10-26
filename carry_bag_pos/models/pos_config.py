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
#############################################################################
from odoo import fields, models


class PosConfig(models.Model):
    """Add bag charge settings to the POS configuration."""
    _inherit = 'pos.config'

    is_bag_charges = fields.Boolean(
        string="Enable Bag Charges",
        help="Enable this to show the 'Add Bag' button in the POS.")
    bag_category_id = fields.Many2one(
        'pos.category',
        help="Products in this POS category are listed as selectable bags.")

    def get_bag_stock(self, template_ids):
        """Return the quantity on hand of the given bag products.

        :param list template_ids: ids of the bag product templates
        :return: dict {template id: quantity on hand}
        """
        self.ensure_one()
        templates = self.env['product.template'].sudo().search([
            ('id', 'in', template_ids),
            ('available_in_pos', '=', True),
            ('company_id', 'in', [False, self.company_id.id]),
        ])
        # Limit the quantity to the warehouse of this POS when it has one.
        warehouse = self.warehouse_id if 'warehouse_id' in self._fields else False
        if warehouse:
            templates = templates.with_context(warehouse_id=warehouse.id)
        return {template.id: template.qty_available for template in templates}
