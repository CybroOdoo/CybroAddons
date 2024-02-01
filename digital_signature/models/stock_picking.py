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
from odoo import fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    """Inherited the stock picking for showing the digital signature
    and company stamp in both report of  picking operations and delivery slip"""
    _inherit = "stock.picking"

    def _default_show_sign(self):
        """ Returns the value of digital sign from inventory setting"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.show_digital_sign_inventory')

    def _default_enable_option(self):
        """Returns the value of enable options  from inventory setting"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.enable_options_inventory')

    def _default_show_stamp(self):
        """Returns the value of company stampfrom inventory setting"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.show_company_stamp_inventory')

    digital_sign = fields.Binary(string='Signature',
                                 help="Signature of inventory "
                                      "management person")
    sign_by = fields.Char(string='Signed By',
                          help="Name of signed person")
    designation = fields.Char(string='Designation',
                              help="Designation for signed person")
    sign_on = fields.Datetime(string='Signed On', help="Date of sign")
    show_sign = fields.Boolean(default=_default_show_sign,
                               compute='_compute_show_sign',
                               help="Field to get the value in setting to "
                                    "current model")
    enable_option = fields.Boolean(default=_default_enable_option,
                                   compute='_compute_enable_option',
                                   help="Field to get the value in setting to "
                                        "current model")
    sign_applicable = fields.Selection([
        ('picking_operations', 'Picking Operations'),
        ('delivery', 'Delivery Slip'),
        ('both', 'Both'),
    ], string="Sign Applicable inside", compute='_compute_sign_applicable',
        help="Field to get the value in setting to current model")

    stamp_applicable = fields.Selection([
        ('picking_stamp', 'Picking Operations'),
        ('delivery_stamp', 'Delivery Slip'),
        ('both_stamp', 'Both')], string="stamp",
        compute='_compute_stamp_applicable')
    show_stamp = fields.Boolean(default=_default_show_stamp,
                                compute='_compute_show_stamp',
                                help="Field to get the value in setting "
                                     "to current model")

    def _compute_show_sign(self):
        """Function to compute the value of digital signature"""
        for record in self:
            record.show_sign = self._default_show_sign()

    def _compute_enable_option(self):
        """Function to compute the value of enable options from the
           inventory setting"""
        for record in self:
            record.enable_option = self._default_enable_option()

    def _compute_sign_applicable(self):
        """Function to compute the value, which report has applied
           the signature"""
        for rec in self:
            rec.sign_applicable = self.env['ir.config_parameter'].sudo(). \
                get_param(
                'digital_signature.sign_applicable')

    def _compute_stamp_applicable(self):
        """Function to compute the value  which report has applied
           the signature"""
        for rec in self:
            rec.stamp_applicable = self.env['ir.config_parameter'].sudo(). \
                get_param(
                'digital_signature.company_stamp_applicable')

    def _compute_show_stamp(self):
        """Function to compute the value  which report has applied the stamp"""
        for stamp in self:
            stamp.show_stamp = self._default_show_stamp()

    def button_validate(self):
        """ Function to validate the signature is missing or not"""
        res = super(StockPicking, self).button_validate()
        if self.env['ir.config_parameter'].sudo().get_param(
                'digital_signature.confirm_sign_inventory') and \
                self.digital_sign is False:
            raise UserError('Signature is missing')
        return res
