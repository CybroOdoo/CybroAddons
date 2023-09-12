# -*- coding: utf-8 -*-
#############################################################################
#
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
from ast import literal_eval
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Adding field in res config settings"""
    _inherit = 'res.config.settings'

    auth_signup_approval = fields.Boolean(string='Signup Approval',
            config_parameter='website_signup_approval.auth_signup_approval',
            help="Signup request send only if it is enabled")
    documents_ids = fields.Many2many('document.attachment', string='Documents',
                                     help="Select the type of document")

    def set_values(self):
        """Set values for the field"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'website_signup_approval.documents_ids',
            self.documents_ids.ids)

    def get_values(self):
        """Return values for the fields"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        limits = params.get_param(
            'website_signup_approval.documents_ids')
        res.update(documents_ids=[
            (6, 0, literal_eval(limits))] if limits else False)
        return res
