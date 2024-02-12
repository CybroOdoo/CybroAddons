# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def _get_contacts_fields_domain(self):
        """To set domain to the field 'unique_contact_ids'"""
        return [
            ('model', '=', 'res.partner'), ('store', '=', True),
            ('ttype', 'in', ['binary', 'char'])]

    is_unique_contact = fields.Boolean(string="Unique Contacts Alert",
                                       help="Is it required that any field "
                                            "in contact be unique?")
    unique_contact_ids = fields.Many2many(
        'ir.model.fields', string='Contact Fields',
        domain=_get_contacts_fields_domain,
        help='Warning to avoid duplication of customer/vendor'
             ' details in the system')

    def set_values(self):
        """Inorder to set values in the setting"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'duplicate_contact_details_alert.is_unique_contact',
            self.is_unique_contact)
        self.env['ir.config_parameter'].set_param(
            'duplicate_contact_details_alert.unique_contact_ids',
            self.unique_contact_ids.ids)

    @api.model
    def get_values(self):
        """Inorder to get values from the settings"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        contact_field_ids = params.get_param(
            'duplicate_contact_details_alert.unique_contact_ids')
        if contact_field_ids:
            res.update(
                is_unique_contact=params.get_param(
                    'duplicate_contact_details_alert.is_unique_contact'),
                unique_contact_ids=[(6, 0, literal_eval(contact_field_ids))],
            )
            return res
        else:
            return res
