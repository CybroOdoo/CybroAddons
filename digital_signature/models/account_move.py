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


class AccountMove(models.Model):
    """Extends the 'account.move' model to support digital signatures
    on invoices."""
    _inherit = "account.move"

    @api.model
    def _default_show_sign(self):
        """Get default value for 'Show Digital Signature' on invoices."""
        return self.env['ir.config_parameter'].sudo().get_bool(
            'digital_signature.is_show_digital_sign_invoice'
        )

    @api.model
    def _default_enable_sign(self):
        """Get default value for 'Enable Digital Signature Options' on
        invoices."""
        return self.env['ir.config_parameter'].sudo().get_bool(
            'digital_signature.is_enable_options_invoice'
        )

    @api.model
    def _default_show_sign_bill(self):
        """Get default value for 'Show Digital Signature on Bills' on
        invoices."""
        return self.env['ir.config_parameter'].sudo().get_bool(
            'digital_signature.is_show_digital_sign_bill'
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
             "on invoices.",
    )
    is_show_sign_bill = fields.Boolean(
        string='Show Signature on Bills',
        default=lambda self: self._default_show_sign_bill(),
        compute='_compute_show_sign_bill',
        help="Determines whether the digital signature should be displayed "
             "on bills.",
    )
    is_enable_others = fields.Boolean(
        string="Enable Others",
        default=lambda self: self._default_enable_sign(),
        compute='_compute_enable_others',
        help="Enables various digital signature options on invoices.",
    )

    def _compute_show_signature(self):
        """Compute the 'Show Signature' field on invoices."""
        is_show_signature = self._default_show_sign()
        for record in self:
            record.is_show_signature = is_show_signature

    def _compute_enable_others(self):
        """Compute the 'Enable Digital Signature Options' field on invoices."""
        is_enable_others = self._default_enable_sign()
        for record in self:
            record.is_enable_others = is_enable_others

    def _compute_show_sign_bill(self):
        """Compute the 'Show Signature on Bills' field on invoices."""
        is_show_sign_bill = self._default_show_sign_bill()
        for record in self:
            record.is_show_sign_bill = is_show_sign_bill

    def action_post(self):
        """Post the invoice, checking for the presence of a signature."""
        res = super().action_post()
        config = self.env['ir.config_parameter'].sudo()
        check_confirm = config.get_bool(
            'digital_signature.is_confirm_sign_invoice'
        )
        show_invoice = config.get_bool(
            'digital_signature.is_show_digital_sign_invoice'
        )
        show_bill = config.get_bool(
            'digital_signature.is_show_digital_sign_bill'
        )

        for move in self:
            if move.move_type == 'out_invoice':
                if check_confirm and show_invoice and not move.digital_sign:
                    raise UserError(self.env._("Signature is missing"))
            elif move.move_type == 'in_invoice':
                if check_confirm and show_bill and not move.digital_sign:
                    raise UserError(self.env._("Signature is missing"))
        return res


