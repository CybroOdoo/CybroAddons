# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError


class InventoryInherit(models.Model):
    _inherit = "stock.picking"

    def _default_show_sign(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.show_digital_sign_inventory')

    def _default_enable_options(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.enable_options_inventory')

    digital_sign = fields.Binary(string='Signature')
    sign_by = fields.Char(string='Signed By')
    designation = fields.Char(string='Designation')
    sign_on = fields.Datetime(string='Signed On')
    show_sign = fields.Boolean(default=_default_show_sign,
                               compute='_compute_show_sign')
    enable_option = fields.Boolean(default=_default_enable_options,
                                   compute='_compute_enable_optiion')
    sign_applicable = fields.Selection([
        ('picking_operations', 'Picking Operations'),
        ('delivery', 'Delivery Slip'),
        ('both', 'Both'),
    ], string="Sign Applicable inside", compute='_compute_sign_applicable')

    def button_validate(self):
        res = super(InventoryInherit, self).button_validate()
        if self.env['ir.config_parameter'].sudo().get_param(
            'digital_signature.confirm_sign_inventory') and self.digital_sign is False:
            raise UserError('Signature is missing')
        return res

    def _compute_show_sign(self):
        show_signature = self._default_show_sign()
        for record in self:
            record.show_sign = show_signature

    def _compute_enable_optiion(self):
        enable_others = self._default_enable_options()
        for record in self:
            record.enable_option = enable_others

    def _compute_sign_applicable(self):
        for rec in self:
            rec.sign_applicable = self.env['ir.config_parameter'].sudo().get_param(
                'digital_signature.sign_applicable')
