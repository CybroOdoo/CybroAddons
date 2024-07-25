# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo import fields, models


class PosConfig(models.Model):
    """ Inherited model for adding new field to configuration settings
    that allows to add lead time to reservations """

    _inherit = 'pos.config'

    has_lead_time = fields.Boolean(
        string='Lead Time',
        compute="_compute_has_lead_time",
        help="Enable to set lead time for reservations")
    has_reservation_charge = fields.Boolean(
        string="Reservation Charge",
        compute="_compute_has_reservation_charge",
        help="Enable to apply charge for reservations.")

    def _compute_has_lead_time(self):
        """ To check whether lead time is enabled from settings """
        if self.env['ir.config_parameter'].sudo().get_param(
                'table_reservation_on_website.is_lead_time'):
            self.has_lead_time = True
        else:
            self.has_lead_time = False

    def _compute_has_reservation_charge(self):
        """ To check whether reservation charge is enabled from settings """
        if self.env['ir.config_parameter'].sudo().get_param(
                'table_reservation_on_website.reservation_charge'):
            self.has_reservation_charge = True
        else:
            self.has_reservation_charge = False
