# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjali VP (Contact : odoo@cybrosys.com)
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
from odoo import models, fields, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    custom_uom_name = fields.Char(string='Custom UoM Name')
    custom_uom_price = fields.Float(string='Custom UoM Price')
    selected_uom_id = fields.Many2one(
        'uom.uom',
        string='Selected UoM',
        help='The unit of measure selected in POS for this order line '
             '(overrides product default UoM for stock moves).'
    )

    @api.model
    def _load_pos_data_fields(self, config):
        """Include custom UoM fields so they are sent to the POS frontend.

        In Odoo 19 the framework reads _load_pos_data_fields to know which
        fields to load from the DB AND to build the JS model field definitions
        (type, relation, etc.) via _load_pos_data_relations.  Only fields
        listed here are included in ormSerialization and therefore synced back
        to the backend on sync_from_ui.
        """
        result = super()._load_pos_data_fields(config)
        result += ['custom_uom_name', 'custom_uom_price', 'selected_uom_id']
        return result
