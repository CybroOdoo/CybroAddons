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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    """Inherited Account Move model to enforce contact approval."""
    _inherit = 'account.move'

    partner_id = fields.Many2one(
        domain="[('company_id', 'in', (False, company_id)), ('state', '=', 'approve')]",
    )

    @api.constrains('partner_id', 'move_type')
    def _check_partner_id_approved(self):
        for move in self:
            if move.is_invoice(include_receipts=True) and move.partner_id and move.partner_id.state != 'approve':
                raise ValidationError(_(
                    "The selected partner '%s' is not approved. "
                    "Please select an approved partner."
                ) % move.partner_id.name)

