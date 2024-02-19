# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class ContactContactSync(models.Model):
    """ Model to synchronize the contacts"""
    _name = 'contact.sync'
    _description = "Contact Sync"

    property_id = fields.Many2one(
        'mailer.cloud.properties',
        required=True, string='Mailer Cloud Properties',
        help='Reference to the Mailer Cloud properties associated with this record.')
    contact_fields = fields.Selection(
        selection=lambda self: self.dynamic_selection(),
        required=True, string='Odoo Fields',
        help='Selection of Odoo fields to be synchronized with Mailer Cloud.')
    sync_id = fields.Many2one(
        'mailer.cloud.api.sync', string='Synchronization',
        help='Reference to the Mailer Cloud API synchronization associated with this record.')

    def dynamic_selection(self):
        """ Generate a dynamic selection for Odoo fields.

        This method dynamically generates a selection list for Odoo fields
        based on the available fields in the 'res.partner' model."""
        return [(key, key.capitalize()) for key in self.env['res.partner'].fields_get().keys()]
