# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ansil pv (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
# Import required libraries (make sure it is installed!)
import logging
from odoo import _, models
from odoo.exceptions import ValidationError
import requests
from wallee import Configuration
from wallee.api import (
    TransactionServiceApi,
    TransactionPaymentPageServiceApi,
    CustomerServiceApi,
)
from wallee.models import (
    LineItem,
    LineItemType,
    TransactionCreate,
    CustomerCreate,
    CustomerPostalAddressCreate,
)

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_specific_rendering_values(self, processing_values):
        """
        For get specific rendering values and execute execute_payment
        function
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "wallee":
            return res
        return self.execute_payment()

    def execute_payment(self):
        """Fetching data and Executing Payment
        :return: The response content."""
        odoo_base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        sale_order = (
            self.env["payment.transaction"]
            .search([("id", "=", self.id)])
            .sale_order_ids
        )
        if self.provider_id.code == "wallee":
            config = Configuration(
                user_id=self.provider_id.wallee_user_id,
                api_secret=self.provider_id.wallee_user_secret_key,
                # set a custom request timeout if needed. (If not set, then the
                # default value is: 25 seconds)
                request_timeout=30,
            )
            transaction_service = TransactionServiceApi(configuration=config)
            customer_service = CustomerServiceApi(configuration=config)
            transaction_payment_page_service = TransactionPaymentPageServiceApi(
                configuration=config
            )
            line_items = []
            for index, lines in enumerate(sale_order.order_line):
                locals()[f"line_item_{index}"] = LineItem(
                    name=lines.product_id.name,
                    unique_id=str(lines.id),
                    sku=lines.product_id.detailed_type,
                    quantity=lines.product_uom_qty,
                    amount_including_tax=lines.price_total,
                    type=LineItemType.PRODUCT,
                )
                line_items.append(locals()[f"line_item_{index}"])
            address_create = CustomerCreate(
                customer_id=str(sale_order.partner_id.id),
                email_address=sale_order.partner_id.email,
                family_name="",
                given_name=sale_order.partner_id.name,
                street=sale_order.partner_id.street,
                postcode=sale_order.partner_id.zip,
                city=sale_order.partner_id.city,
                country=sale_order.partner_id.country_id,
                postal_state=sale_order.partner_id.state_id,
            )

            user_address = CustomerPostalAddressCreate(
                customer_id=str(sale_order.partner_id.id),
                email_address=sale_order.partner_id.email,
                family_name="",
                given_name=sale_order.partner_id.name,
                street=sale_order.partner_id.street,
                postcode=sale_order.partner_id.zip,
                city=sale_order.partner_id.city,
                country=sale_order.partner_id.country_id.name,
                postal_state=sale_order.partner_id.state_id.name,
            )

            # create transaction model
            transaction = TransactionCreate(
                customer_id=sale_order.partner_id.id,
                merchant_reference=sale_order.name,
                invoice_merchant_reference=sale_order.name,
                line_items=line_items,
                auto_confirmation_enabled=True,
                currency=self.env.user.currency_id.name,
                shipping_address=user_address,
                billing_address=user_address,
                failed_url=f"{odoo_base_url}/webhook",
                success_url=f"{odoo_base_url}/webhook",
            )

            transaction_create = transaction_service.create(
                space_id=self.provider_id.wallee_user_space_id, transaction=transaction
            )

            payment_page_url = transaction_payment_page_service.payment_page_url(
                space_id=self.provider_id.wallee_user_space_id, id=transaction_create.id
            )
            self.provider_reference = transaction_create.id
            response = requests.request("POST", payment_page_url)
            return {"api_url": payment_page_url}

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """
        Get payment status from Wallee.

        :param provider_code: The code of the provider handling the transaction
        :param notification_data: The data received from Wallee notification.
        :return: The transaction matching the reference.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "wallee":
            return tx
        reference = notification_data.get("reference")
        if not reference:
            raise ValidationError(
                "Wallee: "
                + _(
                    "No reference found.",
                )
            )
        tx = self.search(
            [
                ("reference", "=", notification_data.get("reference")),
                ("provider_code", "=", "wallee"),
            ]
        )
        if not tx:
            raise ValidationError(
                "Wallee: "
                + _(
                    "No transaction found " "matching reference %s.",
                    notification_data.get("reference"),
                )
            )
        return tx

    def _handle_notification_data(self, provider_code, notification_data):
        """
        Handle the notification data received from Wallee.
        This method retrieves the transaction corresponding to the
        notification data, processes the notification data, and executes the
        callback.
        :param provider_code: The code of the provider handling the transaction
        :param notification_data: The data received from Wallee notification.
        :return: The transaction object.
        """
        tx = self._get_tx_from_notification_data(provider_code, notification_data)
        tx._process_notification_data(notification_data)
        tx._execute_callback()
        return tx

    def _process_notification_data(self, notification_data):
        """
        Process the notification data received from Wallee.

        This method processes the notification data and updates the payment
        state of the transaction accordingly.

        :param notification_data: The data received from Wallee notification.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != "wallee":
            return
        status = notification_data.get("state")
        if status == "FULFILL":
            self._set_done(state_message="Authorised")
        elif status in (
            "COMPLETED",
            "PENDING",
            "CONFIRMED",
            "PROCESSING",
            "AUTHORIZED",
        ):
            self._set_pending(
                state_message="Authorised but on hold for " "further anti-fraud review"
            )
        elif status in ("FAILED", "VOIDED", "DECLINE"):
            self._set_canceled(state_message="Error")
        else:
            _logger.warning(
                "received unrecognized payment state %s for "
                "transaction with reference %s",
                notification_data.get("reference"),
            )
            self._set_error("wallee: " + _("Invalid payment status."))
