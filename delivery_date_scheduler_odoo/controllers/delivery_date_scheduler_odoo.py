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
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from odoo import fields, http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class DeliveryDateScheduler(CustomerPortal):
    """Controller for delivery date scheduling and quotation confirmation in portal."""

    def _get_delivery_date_range(self):
        """Fetch date range configuration parameters and calculate minimum and maximum dates."""
        config_parameter = request.env['ir.config_parameter'].sudo()
        warning_date = bool(config_parameter.get_str(
            'delivery_date_scheduler_odoo.warning_date'))
        if not warning_date:
            return False, False, False
        try:
            min_date = int(config_parameter.get_str(
                'delivery_date_scheduler_odoo.min_date_range') or 0)
        except (ValueError, TypeError):
            min_date = 0
        try:
            max_date = int(config_parameter.get_str(
                'delivery_date_scheduler_odoo.max_date_range') or 0)
        except (ValueError, TypeError):
            max_date = 0
        today_date = fields.Date.today()
        minimum_date = today_date + timedelta(days=min_date)
        maximum_date = today_date + timedelta(days=max_date)
        return True, minimum_date, maximum_date

    @http.route('/delivery_date_schedule', type='jsonrpc', auth='public',
                csrf=False)
    def delivery_date_schedule(self, **kw):
        """
        for checking the user entered delivery date
        """
        warning_date, minimum_date, maximum_date = self._get_delivery_date_range()
        new_maximum_date = False
        new_minimum_date = False
        if warning_date:
            new_maximum_date = maximum_date.strftime("%d-%m-%Y")
            new_minimum_date = minimum_date.strftime("%d-%m-%Y")
            raw_date = kw.get('date')
            delivery_date = False
            if raw_date:
                try:
                    delivery_date = fields.Date.from_string(raw_date)
                except (ValueError, TypeError):
                    delivery_date = False

            if delivery_date and minimum_date <= delivery_date <= maximum_date:
                error_value = 1
            else:
                error_value = 2
        else:
            error_value = 3
        return {
            'error_value': error_value,
            'min_date': new_minimum_date,
            'max_date': new_maximum_date
        }

    @http.route('/confirm_delivery_date_schedule', type='jsonrpc', auth='public',
                csrf=False)
    def confirm_delivery_date_schedule(self, **kw):
        """
        confirm and writing the confirmed quotation
        """
        order_id = kw.get('id')
        if not order_id:
            raise ValidationError(request.env._("Order ID is required."))
        try:
            order_id = int(order_id)
        except (ValueError, TypeError):
            raise ValidationError(request.env._("Invalid order ID."))

        # IDOR prevention & Access check
        order_sudo = self._document_check_access(
            'sale.order', order_id, access_token=kw.get('access_token')
        )

        # State check: Only quotations in 'sent' state can be confirmed
        if order_sudo.state != 'sent':
            raise ValidationError(request.env._("Only sent quotations can be confirmed."))

        # Expiry check
        if order_sudo.is_expired or (
            order_sudo.validity_date and order_sudo.validity_date < fields.Date.today()
        ):
            raise ValidationError(
                request.env._("This quotation has expired and cannot be confirmed.")
            )

        # Signature check
        if order_sudo._has_to_be_signed():
            raise ValidationError(
                request.env._("This quotation requires a signature before confirmation.")
            )

        # Payment check
        if order_sudo._has_to_be_paid():
            raise ValidationError(
                request.env._("This quotation requires payment before confirmation.")
            )

        # Server-side delivery date & range check
        raw_date = kw.get('date')
        if not raw_date:
            raise ValidationError(request.env._("Please provide a delivery date."))
        try:
            delivery_date = fields.Date.from_string(raw_date)
        except (ValueError, TypeError):
            delivery_date = False

        if not delivery_date:
            raise ValidationError(request.env._("Invalid delivery date format."))

        warning_date, minimum_date, maximum_date = self._get_delivery_date_range()
        if warning_date and not (minimum_date <= delivery_date <= maximum_date):
            raise ValidationError(request.env._(
                "The delivery date must be within %(min_date)s and %(max_date)s.",
                min_date=minimum_date.strftime("%d-%m-%Y"),
                max_date=maximum_date.strftime("%d-%m-%Y"),
            ))

        # Timezone-aware conversion for commitment_date
        tz_name = (
            request.env.context.get('tz')
            or request.env.user.tz
            or order_sudo.partner_id.tz
            or order_sudo.company_id.partner_id.tz
            or 'UTC'
        )
        try:
            user_tz = ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, TypeError, ValueError):
            user_tz = UTC
        commitment_datetime = datetime.combine(
            delivery_date, time.min, tzinfo=user_tz
        ).astimezone(UTC).replace(tzinfo=None)

        order_sudo.write({
            'commitment_date': commitment_datetime,
            'user_description': kw.get('description'),
        })
        order_sudo.action_confirm()
        return True
