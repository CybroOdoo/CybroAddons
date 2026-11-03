# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER 
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    """Extends the 'purchase.order' model to support digital signatures
    on purchase orders."""
    _inherit = "purchase.order"

    @api.model
    def _default_show_sign(self):
        """Get the default value for the 'Show Digital Signature' field on
        purchase orders."""
        return self.env['ir.config_parameter'].sudo().get_str(
            'digital_signature.is_show_digital_sign_po'
        )

    @api.model
    def _default_enable_sign(self):
        """Get the default value for the 'Enable Digital Signature Options'
        field on purchase orders."""
        return self.env['ir.config_parameter'].sudo().get_str(
            'digital_signature.is_enable_options_po'
        )

    digital_sign = fields.Binary(
        string='Digital Signature',
        help="Binary field to store digital signatures.",
    )
    sign_by = fields.Char(
        string='Signed By',
        help="Name of the person who signed the document.",
    )
    designation = fields.Char(
        help="Designation of the person who signed the document.",
    )
    sign_on = fields.Datetime(
        string='Signed On',
        help="Date and time when the document was signed.",
    )
    is_show_signature = fields.Boolean(
        string='Show Signature',
        default=lambda self: self._default_show_sign(),
        compute='_compute_show_signature',
        help="Determines whether the digital signature should be displayed "
             "on purchase orders.",
    )
    is_enable_others = fields.Boolean(
        string="Enable Others",
        default=lambda self: self._default_enable_sign(),
        compute='_compute_enable_others',
        help="Enables various digital signature options on purchase orders.",
    )

    def button_confirm(self):
        """Override confirm button to add error if signature is missing."""
        if self.env['ir.config_parameter'].sudo().get_bool(
            'digital_signature.is_confirm_sign_po'
        ):
            for order in self:
                if not order.digital_sign:
                    raise UserError(self.env._("Signature is missing"))
        return super().button_confirm()

    def _compute_show_signature(self):
        """Compute the 'Show Signature' field on purchase orders."""
        is_show_signature = self._default_show_sign()
        for record in self:
            record.is_show_signature = is_show_signature

    def _compute_enable_others(self):
        """Compute the 'Enable Digital Signature Options' field."""
        is_enable_others = self._default_enable_sign()
        for record in self:
            record.is_enable_others = is_enable_others

