# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
from odoo import api, fields, models


class RestaurantTable(models.Model):
    """ Inherit restaurant table for adding rate field """
    _inherit = 'restaurant.table'

    rate = fields.Float(string="Amount",
                        help="Amount for reservation of this table")

    is_show_field = fields.Boolean(string='Show field',
                                   compute='_compute_is_show_field',
                                   help='Depends on the field value field '
                                        'rate visibility is determined')

    @api.depends_context('table_reservation_on_website.reservation_charge')
    def _compute_is_show_field(self):
        """Compute field rate visibility using this function"""
        for record in self:
            if record.env['ir.config_parameter'].get_param(
                    'table_reservation_on_website.reservation_charge'):
                record.is_show_field = True
            else:
                record.is_show_field = False
