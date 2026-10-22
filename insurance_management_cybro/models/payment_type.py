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
from odoo import api, fields, models
from odoo.exceptions import UserError


class PaymentType(models.Model):
    """Defines the payment methods supported by the policies."""
    _name = 'payment.type'
    _description = 'Payment Type'

    name = fields.Char(string="Payment Type", required=True,
                       help="Name of the payment type")

    @api.ondelete(at_uninstall=False)
    def _unlink_except_system_types(self):
        """The fixed and installment types drive the invoicing logic."""
        system_types = self.env['payment.type']
        for xmlid in ('payment_type_fixed', 'payment_type_installment'):
            system_types |= self.env.ref(
                f'insurance_management_cybro.{xmlid}',
                raise_if_not_found=False) or self.env['payment.type']
        if self & system_types:
            raise UserError(self.env._(
                "The Fixed and Installment payment types cannot be deleted."))
