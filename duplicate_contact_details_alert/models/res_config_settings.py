# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
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
    """Inherit res.config.settings to add settings for unique contact fields."""
    _inherit = 'res.config.settings'

    def _get_contacts_fields_domain(self):
        """To set domain to the field 'unique_contact_ids'."""
        return [
            ('model', '=', 'res.partner'), ('store', '=', True),
            ('ttype', 'in', ['binary', 'char'])]

    is_unique_contact = fields.Boolean(
        string="Unique Contacts Alert",
        help="Is it required that any field in contact be unique?")
    unique_contact_ids = fields.Many2many(
        'ir.model.fields', string='Contact Fields',
        domain=lambda self: self._get_contacts_fields_domain(),
        help='Warning to avoid duplication of customer or vendor '
             'details in the system.')

    def set_values(self):
        """In order to set values in the settings."""
        res = super().set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_bool(
            'duplicate_contact_details_alert.is_unique_contact',
            self.is_unique_contact)
        if self.is_unique_contact:
            ICP.set_str(
                'duplicate_contact_details_alert.unique_contact_ids',
                str(self.unique_contact_ids.ids))
        else:
            ICP.set_str(
                'duplicate_contact_details_alert.unique_contact_ids',
                '[]')
        return res

    @api.model
    def get_values(self):
        """In order to get values from the settings."""
        res = super().get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        contact_field_ids = ICP.get_str(
            'duplicate_contact_details_alert.unique_contact_ids', '')
        is_unique_contact = ICP.get_bool(
            'duplicate_contact_details_alert.is_unique_contact', False)
        fields_list = literal_eval(contact_field_ids) if contact_field_ids else []
        valid_ids = self.env['ir.model.fields'].sudo().browse(fields_list).exists().ids if fields_list else []
        res.update(
            is_unique_contact=is_unique_contact,
            unique_contact_ids=[(6, 0, valid_ids)] if valid_ids else False,
        )
        return res
