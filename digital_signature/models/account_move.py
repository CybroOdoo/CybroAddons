# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj @cybrosys(odoo@cybrosys.com)
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """ Extends the 'account.move' model to support digital signatures
    on invoices."""
    _inherit = "account.move"

    @api.model
    def _default_show_sign(self):
        """Get the default value for the 'Show Digital Signature' field on
        invoices."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.is_show_digital_sign_invoice')

    @api.model
    def _default_enable_sign(self):
        """Get the default value for the 'Enable Digital Signature Options'
        field on invoices."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.is_enable_options_invoice')

    @api.model
    def _default_show_sign_bill(self):
        """Get the default value for the 'Show Digital Signature on Bills'
        field on invoices."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.is_show_digital_sign_bill')

    digital_sign = fields.Binary(string='Signature', help="Binary field to "
                                                          "store digital "
                                                          "signatures.")
    sign_by = fields.Char(string='Signed By', help="Name of the person who "
                                                   "signed the document.")
    designation = fields.Char(string='Designation', help="Designation of the "
                                                         "person who signed "
                                                         "the document.")
    sign_on = fields.Datetime(string='Signed On', help="Date and time when the "
                                                       "document was signed.")
    is_show_signature = fields.Boolean(string='Show Signature',
                                       default=_default_show_sign,
                                       compute='_compute_show_signature',
                                       help="Determines whether the digital "
                                            "signature should be displayed "
                                            "on invoices.")
    is_show_sign_bill = fields.Boolean(string='Show Signature on Bills',
                                       default=_default_show_sign_bill,
                                       compute='_compute_show_sign_bill',
                                       help="Determines whether the digital "
                                            "signature should be displayed "
                                            "on bills.")
    is_enable_others = fields.Boolean(string="Enable Others",
                                      default=_default_enable_sign,
                                      compute='_compute_enable_others',
                                      help="Enables various digital signature "
                                           "options on invoices.")

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
            record.show_sign_bill = is_show_sign_bill

    def action_invoice_sent(self):
        """Send the invoice and validate it, checking for the presence of a
        digital signature."""
        res = super(AccountMove, self).action_invoice_sent()
        if self.env[
            'ir.config_parameter'].sudo().get_param(
            'digital_signature.is_confirm_sign_invoice') and \
                self.digital_sign is False:
            raise UserError(_("Signature is missing"))
        return res
