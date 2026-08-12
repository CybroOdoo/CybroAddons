# -*- coding: utf-8 -*-
#############################################################################
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
# ############################################################################

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

class StockPickingCustody(models.Model):
    """
    Extends stock.picking with custody transfer integration.

    Lifecycle:
      1. Picking reaches Ready (state='assigned') + is_oil_gas_transfer=True
         → Draft custody.transfer auto-created.
      2. Operator prepares and Approves the custody transfer.
      3. button_validate() is blocked until CT is in 'approved' (or 'in_progress').
      4. Once picking is validated (done), CT is auto-completed with actual
         quantities from the done stock moves.
    """
    _inherit = "stock.picking"

    custody_transfer_id = fields.Many2one(
        "custody.transfer",
        string="Custody Transfer",
        readonly=True,
        copy=False,
        help="Draft custody transfer auto-created when this oil & gas transfer "
             "reaches Ready state. Must be Approved before validation is allowed.",
    )
    custody_transfer_count = fields.Integer(
        compute="_compute_custody_transfer_count",
        string="Custody Transfers", help="Specify the numerical measurement, volume, or financial amount for 'custody transfers'.",
    )

    def _compute_custody_transfer_count(self):
        """Calculates and updates the 'transfer count' value automatically based on related operational inputs."""
        for picking in self:
            picking.custody_transfer_count = 1 if picking.custody_transfer_id else 0

    def action_create_custody_transfer(self):
        """Manually create a custody transfer from the picking form."""
        for picking in self:
            if not picking.is_oil_gas_transfer:
                raise UserError(_("This transfer is not marked as an Oil and Gas Transfer."))
            if picking.custody_transfer_id:
                raise UserError(_("A custody transfer has already been created for this transfer."))

            custody = picking.with_context(
                _custody_transfer_creating=True
            )._auto_create_custody_transfer()
            if custody:
                picking.with_context(_custody_transfer_creating=True).write(
                    {"custody_transfer_id": custody.id}
                )

        if len(self) == 1 and self.custody_transfer_id:
            return {
                "type": "ir.actions.act_window",
                "name": _("Custody Transfer"),
                "res_model": "custody.transfer",
                "res_id": self.custody_transfer_id.id,
                "view_mode": "form",
                "target": "current",
            }
        return True

    # -------------------------------------------------------------------------
    # button_validate() — gate on CT approval; auto-complete after validation
    # -------------------------------------------------------------------------
    def button_validate(self):
        """
        - Block validation if the linked custody transfer is not yet approved.
        - After successful validation, auto-complete the custody transfer.
        """
        # Gate check BEFORE calling super()
        for picking in self:
            if not picking.is_oil_gas_transfer:
                continue
            ct = picking.custody_transfer_id
            if not ct:
                continue
            if ct.state in ("draft", "cancelled", "disputed"):
                raise UserError(
                    _(
                        "The stock transfer '%(picking)s' cannot be validated.\n\n"
                        "The linked Custody Transfer '%(ct)s' is in %(state)s state. "
                        "It cannot be validated when the Custody Transfer is in Draft, Cancelled, or Disputed states.",
                        picking=picking.name,
                        ct=ct.name,
                        state=dict(ct._fields["state"].selection).get(ct.state, ct.state),
                    )
                )

        result = super().button_validate()

        # Auto-complete CT for pickings that are now done
        for picking in self.filtered(lambda p: p.state == "done" and p.is_oil_gas_transfer):
            if picking.custody_transfer_id:
                picking._auto_complete_custody_transfer()

        return result

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def _auto_create_custody_transfer(self):
        """
        Build a draft custody.transfer from this picking's current data.
        Called automatically when the picking reaches Ready state.
        """
        self.ensure_one()
        vals = {
            "state": "draft",
            "picking_id": self.id,
        }

        if self.picking_type_id:
            vals["picking_type_id"] = self.picking_type_id.id

        # Locations
        if self.location_id:
            vals["source_location_id"] = self.location_id.id
        if self.location_dest_id:
            vals["destination_location_id"] = self.location_dest_id.id

        # Date — prefer scheduled_date
        transfer_date = self.scheduled_date or fields.Datetime.now()
        if self.is_pipeline_transfer and self.pipeline_delivery_start:
            transfer_date = self.pipeline_delivery_start
        vals["transfer_date"] = transfer_date


        # Ownership: skip for internal transfers and manufacturing operations.
        # picking_type_id.code values: 'incoming', 'outgoing', 'internal', 'mrp_operation'
        SKIP_OWNERSHIP_CODES = ("internal", "mrp_operation")
        is_external = (
            self.picking_type_id.code not in SKIP_OWNERSHIP_CODES
            if self.picking_type_id
            else True
        )
        if is_external and self.partner_id:
            vals["owner_partner_id"] = self.partner_id.id
            vals["custodian_partner_id"] = self.partner_id.id

        if self.is_pipeline_transfer:
            vals["transfer_purpose"] = "pipeline_injection"
            if self.carrier_id and self.carrier_id.pipeline_operator:
                vals["carrier_partner_id"] = self.carrier_id.pipeline_operator.id
                vals["operator_partner_id"] = self.carrier_id.pipeline_operator.id
            if self.nomination_id:
                vals["nomination_id"] = self.nomination_id.id
        else:
            # Carrier from driver_id (hr.employee → work_contact_id res.partner)
            if hasattr(self, "driver_id") and self.driver_id and self.driver_id.work_contact_id:
                vals["carrier_partner_id"] = self.driver_id.work_contact_id.id
            elif hasattr(self, "vehicle_id") and self.vehicle_id and self.vehicle_id.driver_id:
                # Fallback: fleet vehicle's driver (res.partner)
                vals["carrier_partner_id"] = self.vehicle_id.driver_id.id

        # Reference from picking name
        if self.name and self.name != "/":
            vals["reference"] = self.name

        # Lines from assigned stock moves (planned quantities)
        line_vals = []
        for move in self.move_ids.filtered(
            lambda m: m.state not in ("cancel", "done") and m.product_id
        ):
            line_vals.append((0, 0, {
                "product_id": move.product_id.id,
                "product_uom_id": move.product_uom.id,
                "planned_qty": move.product_uom_qty,
                "actual_qty": move.quantity,
            }))
        if line_vals:
            vals["line_ids"] = line_vals

        custody = self.env["custody.transfer"].create(vals)

        # Notify via chatter
        self.message_post(
            body=_(
                "Custody Transfer <a href='/web#id=%(id)s&model=custody.transfer'>"
                "<b>%(name)s</b></a> has been automatically created in Draft.",
                id=custody.id,
                name=custody.name,
            ),
            message_type="notification",
        )
        return custody

    def _auto_complete_custody_transfer(self):
        """
        Pull actual quantities from validated stock moves into the CT lines,
        then move the CT to 'completed' state.
        Called automatically after button_validate() succeeds.
        """
        self.ensure_one()
        ct = self.custody_transfer_id
        if not ct or ct.state not in ("approved", "in_progress"):
            return

        # Update actual quantities on matching CT lines
        done_moves = self.move_ids.filtered(lambda m: m.state == "done" and m.product_id)
        for move in done_moves:
            matching_lines = ct.line_ids.filtered(
                lambda l: l.product_id == move.product_id
            )
            if matching_lines:
                matching_lines[0].write({
                    "actual_qty": move.quantity,
                })

        # Complete the custody transfer
        now = fields.Datetime.now()
        ct.write({
            "state": "completed",
            "is_locked": True,
            "completed_by": self.env.user.id,
            "completed_date": now,
        })
        ct._log_event(
            "state_change",
            _(
                "Automatically completed when stock transfer %(name)s was validated.",
                name=self.name,
            ),
        )

        # Notify chatter
        ct.message_post(
            body=_(
                "Custody Transfer automatically completed after stock transfer "
                "<b>%(name)s</b> was validated. Actual quantities updated from done moves.",
                name=self.name,
            ),
            message_type="notification",
        )

    def action_view_custody_transfer(self):
        """Open the linked custody transfer form."""
        self.ensure_one()
        if not self.custody_transfer_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("Custody Transfer"),
            "res_model": "custody.transfer",
            "res_id": self.custody_transfer_id.id,
            "view_mode": "form",
            "target": "current",
        }
