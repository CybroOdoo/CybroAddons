# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    """In this class we are inheriting the model 'sale order' and adding
        a new field for signature"""
    _inherit = 'sale.order'

    sale_person_signature = fields.Binary(string='Signature',
                                          help="Field for adding the "
                                               "signature of the sales"
                                               "person")
    check_signature = fields.Boolean(compute='_compute_check_signature',
                                     help="Check if user is salesperson and "
                                          "settings field "
                                          "'sale_document_approve'"
                                          " is enabled",
                                     string="Check Signature")
    user_salesperson = fields.Boolean(string="User Salesperson",
                                      compute="_compute_user_salesperson",
                                      help="Check if user is salesperson")
    settings_approval = fields.Boolean(string="Sale approval enabled",
                                       compute="_compute_settings_approval",
                                       help="Check if sale approval enabled")

    @api.depends('user_salesperson')
    def _compute_settings_approval(self):
        """Computes the settings_approval field based on settings field."""
        for rec in self:
            rec.settings_approval = True if rec.env[
                'ir.config_parameter'].sudo().get_param(
                'sale.sale_document_approve') else False

    @api.depends('user_salesperson')
    def _compute_user_salesperson(self):
        """Computes the user_salesperson field based on login user"""
        for rec in self:
            rec.user_salesperson = True if rec.env[
                                               'ir.config_parameter'].sudo().get_param(
                'sale.sale_document_approve') and rec.user_id == rec.env.user else False

    @api.depends('user_salesperson')
    def _compute_check_signature(self):
        """In this function computes the value of the boolean field check
        signature which is used to hide/unhidden the validate button in the
         current document"""
        for rec in self:
            rec.check_signature = True if rec.env[
                                              'ir.config_parameter'].sudo().get_param(
                'sale.sale_document_approve') and rec.sale_person_signature else False
