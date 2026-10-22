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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import models
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    """Enforce server-side checks for POS feature restrictions."""
    _inherit = 'pos.order'

    def _check_pos_feature_restrictions(self):
        """Verify that payment and discount restrictions are respected by the cashier."""
        for order in self:
            config = order.session_id.config_id
            manager_ids = set()
            if config:
                for field in ('manager_employee_ids', 'advanced_employee_ids'):
                    if hasattr(config, field):
                        manager_ids.update(getattr(config, field).ids)

            employee = order.employee_id
            user = order.user_id

            # Advanced rights / manager employees bypass restrictions
            if employee and employee.id in manager_ids:
                continue

            # Check payment restriction
            allow_payments = True
            if user and not user.pos_allow_payments:
                allow_payments = False
            if employee and not employee.pos_allow_payments:
                allow_payments = False

            if not allow_payments and order.payment_ids:
                raise ValidationError(self.env._("The cashier is not allowed to process payments."))

            # Check discount restriction
            allow_discount = True
            if user and not user.pos_allow_discount:
                allow_discount = False
            if employee and not employee.pos_allow_discount:
                allow_discount = False

            if not allow_discount and any(line.discount for line in order.lines):
                raise ValidationError(self.env._("The cashier is not allowed to apply discounts."))

    def _process_saved_order(self, draft):
        """Enforce restrictions before processing and marking saved order as paid."""
        self._check_pos_feature_restrictions()
        return super()._process_saved_order(draft)
