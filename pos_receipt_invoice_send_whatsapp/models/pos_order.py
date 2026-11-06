###############################################################################
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
###############################################################################
# pylint: disable=missing-module-docstring,unknown-option-value,too-few-public-methods,protected-access,too-many-locals
import base64

import requests

from odoo import fields, models
from odoo.exceptions import UserError


class PosOrder(models.Model):
    """Inherit the pos_order model to implement the functionality of sending
    invoices and receipts by calling the UltraMsg API."""

    _inherit = "pos.order"

    def action_send_receipt_whatsapp(self, phone):
        """Sends a receipt on WhatsApp using UltraMsg API."""
        self.ensure_one()
        phone = phone or self.partner_id.whatsapp_number
        if not phone:
            raise UserError(self.env._(
                "Wrong inputs detected. This may be due to whatsapp number is not given.",
            ))

        instant = self.env["configuration.manager"].search(
            [
                ("state", "=", "verified"),
                ("config_id", "=", self.config_id.id),
            ],
            limit=1,
        )
        if not instant:
            raise UserError(self.env._(
                "WhatsApp API is not configured or verified for this POS.",
            ))

        ticket_image = self.order_receipt_generate_image()
        filename = f"Receipt-{self.name}.jpg"
        receipt = self.env["ir.attachment"].create(
            {
                "name": filename,
                "type": "binary",
                "raw": ticket_image,
                "res_model": "pos.order",
                "res_id": self.id,
                "mimetype": "image/jpeg",
            },
        )
        url = f"https://api.ultramsg.com/{instant.instance}/messages/document"
        doc_data = (
            base64.b64encode(receipt.raw).decode("utf-8")
            if receipt.raw
            else ""
        )
        payload = {
            "token": instant.token,
            "to": phone,
            "filename": receipt.name,
            "document": doc_data,
            "caption": "Your Receipt is here",
        }
        headers = {"content-type": "application/x-www-form-urlencoded"}
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            response.raise_for_status()
            if response.status_code == 200:
                self.env["whatsapp.message"].create(
                    {
                        "status": "sent",
                        "from_user_id": self.env.user.id,
                        "to_user": phone,
                        "user_name": self.partner_id.name or phone,
                        "body": "Your Receipt is here",
                        "attachment_id": receipt.id,
                        "date_and_time_sent": fields.Datetime.now(),
                    },
                )
        except requests.RequestException as e:
            raise UserError(self.env._(
                "Failed to send WhatsApp message: %s", str(e),
            )) from e

    def action_send_invoice_whatsapp(self, phone):
        """Sends an invoice to the customer via WhatsApp using UltraMsg API."""
        self.ensure_one()
        phone = phone or self.partner_id.whatsapp_number
        if not phone:
            raise UserError(self.env._(
                "Wrong inputs detected. This may be due to whatsapp number is not given.",
            ))

        instant = self.env["configuration.manager"].search(
            [
                ("state", "=", "verified"),
                ("config_id", "=", self.config_id.id),
            ],
            limit=1,
        )
        if not instant:
            raise UserError(self.env._(
                "WhatsApp API is not configured or verified for this POS.",
            ))

        if not self.account_move:
            self.action_pos_order_invoice()
        if not self.account_move:
            raise UserError(
                self.env._("Could not find or generate an invoice for this order."),
            )

        attachment_id = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "mail.message"),
                ("res_id", "in", self.account_move.message_ids.ids),
            ],
            limit=1,
        )
        if not attachment_id:
            report = self.env["ir.actions.report"]._render_qweb_pdf(
                "account.account_invoices",
                self.account_move.ids,
            )
            attachment_id = self.env["ir.attachment"].create(
                {
                    "name": f"Invoice-{self.name}.pdf",
                    "type": "binary",
                    "raw": report[0],
                    "mimetype": "application/pdf",
                },
            )
        url = f"https://api.ultramsg.com/{instant.instance}/messages/document"
        doc_data = (
            base64.b64encode(attachment_id.raw).decode("utf-8")
            if attachment_id.raw
            else ""
        )
        payload = {
            "token": instant.token,
            "to": phone,
            "filename": attachment_id.name,
            "document": doc_data,
            "caption": "Your Invoice is here",
        }
        headers = {"content-type": "application/x-www-form-urlencoded"}
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            response.raise_for_status()
            if response.status_code == 200:
                self.env["whatsapp.message"].create(
                    {
                        "status": "sent",
                        "from_user_id": self.env.user.id,
                        "to_user": phone,
                        "user_name": self.partner_id.name or phone,
                        "body": "Your Invoice is here",
                        "attachment_id": attachment_id.id,
                        "date_and_time_sent": fields.Datetime.now(),
                    },
                )
        except requests.RequestException as e:
            raise UserError(self.env._(
                "Failed to send WhatsApp message: %s", str(e),
            )) from e

    def action_send_invoice(self, **kwargs):
        """Backward compatible helper for sending invoice via WhatsApp."""
        number = kwargs.get("number")
        order_id = kwargs.get("order_id")
        order = self.browse(order_id) if order_id else self
        return order.action_send_invoice_whatsapp(number)

    def action_send_receipt(self, *args, **kwargs):
        """Preserve core action_send_receipt(email) while allowing legacy calls."""
        if len(args) == 1 and isinstance(args[0], str) and "@" in args[0]:
            return super().action_send_receipt(args[0])
        if len(args) == 1 and not kwargs:
            return super().action_send_receipt(args[0])
        return super().action_send_receipt(*args, **kwargs)

    def get_instance(self, **kwargs):
        """Retrieves the verified configuration instance."""
        instant = self.env["configuration.manager"].search(
            [
                ("state", "=", "verified"),
                ("config_id", "=", kwargs.get("config_id")),
            ],
            limit=1,
        )
        return {
            "instant_id": instant.id,
        }
