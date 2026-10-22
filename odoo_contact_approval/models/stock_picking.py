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


class StockPicking(models.Model):
    """Inherited the Stock Picking model to add additional features."""
    _inherit = 'stock.picking'

    partner_id = fields.Many2one(
        domain="[('state', '=', 'approve')]",
    )

    @api.constrains('partner_id')
    def _check_partner_id_approved(self):
        for picking in self:
            if picking.partner_id and picking.partner_id.state != 'approve':
                raise ValidationError(_(
                    "The selected contact '%s' is not approved. "
                    "Please select an approved contact."
                ) % picking.partner_id.name)
