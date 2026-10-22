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


class PurchaseOrder(models.Model):
    """Customization of Purchase Order model to add additional features."""
    _inherit = 'purchase.order'

    partner_id = fields.Many2one(
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('state', '=', 'approve')]",
    )

    @api.constrains('partner_id')
    def _check_partner_id_approved(self):
        for order in self:
            if order.partner_id and order.partner_id.state != 'approve':
                raise ValidationError(_(
                    "The selected vendor '%s' is not approved. "
                    "Please select an approved vendor."
                ) % order.partner_id.name)
