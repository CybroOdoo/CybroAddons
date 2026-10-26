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
from odoo import api, Command, fields, models


class SaleOrder(models.Model):
    """This class inherits the sale.order model to add versioning fields and methods."""
    _inherit = "sale.order"

    is_version = fields.Boolean(
        copy=False,
        help="Indicates whether this record is a version of a main sale order",
    )
    version_count = fields.Integer(
        string="Sale Version Count",
        compute="_compute_version_ids",
        help="Count of versions created for this sale order",
    )
    current_version_id = fields.Many2one(
        comodel_name="sale.order",
        string="Main Order",
        copy=False,
        index=True,
        ondelete="cascade",
        help="The main sale order for which this record is a version",
    )
    version_ids = fields.One2many(
        comodel_name="sale.order",
        inverse_name="current_version_id",
        string="Versions",
        help="All versions created from this sale order",
    )

    @api.depends("version_ids")
    def _compute_version_ids(self):
        """Calculate the number of versions created."""
        for sale in self:
            sale.version_count = len(sale.version_ids)

    def action_create_versions(self):
        """Create a new revision/version of the quotation."""
        self.ensure_one()
        version_num = len(self.version_ids) + 1
        version_name = f"{self.name}-{version_num}"

        sale_order_copy = self.copy(
            default={
                "name": version_name,
                "is_version": True,
                "current_version_id": self.id,
                "state": "draft",
                "origin": self.name,
            }
        )
        sale_order_copy.write(
            {
                "order_line": [
                    Command.create(
                        {
                            "display_type": "line_note",
                            "name": self.env._("This is version %s", version_num),
                            "sequence": 0,
                        }
                    )
                ]
            }
        )

    def action_view_versions(self):
        """Action for viewing created versions in list/kanban/form views."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Sale Order Versions"),
            "res_model": self._name,
            "view_mode": "list,kanban,form",
            "domain": [("id", "in", self.version_ids.ids)],
            "context": {
                "default_current_version_id": self.id,
                "default_is_version": True,
            },
            "target": "current",
        }

    def action_confirm(self):
        """Override action_confirm to promote confirmed version and cancel others."""
        res = super().action_confirm()
        for order in self:
            if order.is_version and order.current_version_id:
                parent_order = order.current_version_id
                old_parent_name = parent_order.name
                current_version_name = order.name

                sibling_versions = parent_order.version_ids - order

                # Cancel parent order and convert it into a version of the newly confirmed order
                parent_order._action_cancel()
                parent_order.write(
                    {
                        "name": current_version_name,
                        "is_version": True,
                        "current_version_id": order.id,
                    }
                )

                # Cancel sibling versions and re-link them to the confirmed order
                for sibling in sibling_versions:
                    if sibling.state != "cancel":
                        sibling._action_cancel()
                    sibling.write(
                        {
                            "current_version_id": order.id,
                        }
                    )

                # Promote current order to main sale order
                order.write(
                    {
                        "name": old_parent_name,
                        "is_version": False,
                        "current_version_id": False,
                    }
                )
            else:
                # Main order confirmed: cancel all active versions
                for version in order.version_ids.filtered(lambda v: v.state != "cancel"):
                    version._action_cancel()
        return res
