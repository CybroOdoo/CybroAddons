# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Inherited the account move model for showing the digital signature
      and company stamp in both invoice and bill"""
    _inherit = "account.move"
    _description = 'Account Move'

    @api.model
    def _default_show_signature(self):
        """ Returns the value of digital sign from Invoice setting
         for invoice"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.show_digital_sign_invoice')

    @api.model
    def _default_enable_sign(self):
        """Returns the value of enable options from Invoice setting"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.enable_options_invoice')

    @api.model
    def _default_show_sign_bill(self):
        """ Returns the value of signature from Invoice setting for bill"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.show_digital_sign_bill')

    @api.model
    def _default_show_stamp_invoice(self):
        """ Returns the value of company stamp from Invoice setting
                for invoice"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.show_company_stamp_invoice')

    @api.model
    def _default_show_stamp_bill(self):
        """ Returns the value of company stamp from Invoice setting
                        for bill"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.show_company_stamp_bill')

    digital_sign = fields.Binary(string='Signature',
                                 help="Signature of accounting management "
                                      "person")
    sign_by = fields.Char(string='Signed By', help="Name of signed person")
    designation = fields.Char(string='Designation',
                              help="Designation for signed person")
    sign_on = fields.Datetime(string='Signed On', help="Date of sign")
    show_signature = fields.Boolean('Show Signature',
                                    default=_default_show_signature,
                                    compute='_compute_show_signature',
                                    help="Field to get the value in setting"
                                         " to current model")
    show_sign_bill = fields.Boolean('Show Signature',
                                    default=_default_show_sign_bill,
                                    compute='_compute_show_sign_bill',
                                    help="Field to get the value in setting to "
                                         "current model")
    enable_others = fields.Boolean(default=_default_enable_sign,
                                   compute='_compute_enable_others',
                                   help="Field to get the value in setting to "
                                        "current model")
    show_stamp_invoice = fields.Boolean(default=_default_show_stamp_invoice,
                                        compute='_compute_show_stamp_invoice',
                                        help="Field to get the value in setting"
                                             " to current model")
    stamp_invoicing = fields.Selection([
        ('customer_invoice', 'Customer Invoice'),
        ('vendor_bill', 'Vendor Bill'), ('both', 'Both'),
    ], string="Company Stamp Applicable",
        compute='_compute_stamp_invoicing', help="Field to get the value in "
                                                 "setting to current model")

    def _compute_show_signature(self):
        """ Compute the value of digital signature"""
        for record in self:
            record.show_signature = self._default_show_signature()

    def _compute_enable_others(self):
        """ Compute the value of enable options from the invoicing setting"""
        for record in self:
            record.enable_others = self._default_enable_sign()

    def _compute_show_sign_bill(self):
        """ Compute the value of digital signature in bill"""
        for record in self:
            record.show_sign_bill = self._default_show_sign_bill()

    def _compute_stamp_invoicing(self):
        """ Compute the value, which report has applied the stamp"""
        for invoice in self:
            invoice.stamp_invoicing = self.env['ir.config_parameter']. \
                sudo().get_param(
                'digital_signature.company_stamp_applicable_invoicing')

    def _compute_show_stamp_invoice(self):
        """ Compute the value of company stamp"""
        for invoice in self:
            invoice.show_stamp_invoice = self._default_show_stamp_invoice()

    def action_post(self):
        """Validate the signature is missing or not"""
        res = super(AccountMove, self).action_post()
        if self.env[
            'ir.config_parameter'].sudo().get_param(
            'digital_signature.confirm_sign_invoice') and \
                self.digital_sign is False:
            raise UserError(_("Signature is missing"))
        return res
