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


class PurchaseOrder(models.Model):
    """Inherited the purchase order model for showing the digital signature
      and company stamp in the purchase report"""
    _inherit = "purchase.order"
    _description = 'Purchase Order'

    @api.model
    def _default_show_sign(self):
        """ Returns the value of digital sign from Purchase setting"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.show_digital_sign_po')

    @api.model
    def _default_enable_sign(self):
        """Returns the value of enable options  from Purchase setting"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.enable_options_po')

    @api.model
    def _default_show_stamp_po(self):
        """ Returns the value of company stamp from purchase setting"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.show_company_stamp_po')

    digital_sign = fields.Binary(string='Signature', help="Signature of "
                                                          "purchase management"
                                                          "person")
    sign_by = fields.Char(string='Signed By', help="Name of signed person")
    designation = fields.Char(string='Designation',
                              help="Designation for signed person")
    sign_on = fields.Datetime(string='Signed On', help="Date of sign")
    show_signature = fields.Boolean('Show Signature',
                                    default=_default_show_sign,
                                    compute='_compute_show_signature',
                                    help="Field to get the value in setting to "
                                         "current model")
    enable_sign = fields.Boolean(default=_default_enable_sign,
                                 compute='_compute_enable_sign',
                                 help="Field to get the value in setting to "
                                      "current model")
    show_stamp_po = fields.Boolean(default=_default_show_stamp_po,
                                   compute='_compute_show_stamp_po',
                                   help="Field to get the value in setting to "
                                        "current model")

    def _compute_show_signature(self):
        """ Compute the value of digital signature"""
        for record in self:
            record.show_signature = self._default_show_sign()

    def _compute_enable_sign(self):
        """ Compute the value of enable options from the purchase settings"""
        for record in self:
            record.enable_sign = self._default_enable_sign()

    def _compute_show_stamp_po(self):
        """ Compute the value of company stamp"""
        for record in self:
            record.show_stamp_po = self._default_show_stamp_po()

    def button_confirm(self):
        """Validate the signature is missing or not"""
        res = super(PurchaseOrder, self).button_confirm()
        if self.env[
            'ir.config_parameter'].sudo(). \
                get_param('digital_signature.confirm_sign_po') \
                and self.digital_sign is False:
            raise UserError(_("Signature is missing"))
        return res
