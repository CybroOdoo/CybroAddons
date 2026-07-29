# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class FlynovaExtraService(models.Model):
    """Define optional extra services selectable during Flynova bookings."""

    _name = 'flynova.extra.service'
    _description = 'Flynova Extra Service'
    _order = 'sequence, name'

    name = fields.Char(
        string='Service Name', required=True,
        help='Service name shown to customers on the booking page, e.g. "Airport Transfer".')
    description = fields.Char(
        string='Short Description',
        help='Brief description of the service shown alongside its name on the booking form.')
    price = fields.Float(
        string='Price', required=True, digits=(10, 2),
        help='Cost per booking added to the order total when the customer selects this service.')
    sequence = fields.Integer(
        string='Sequence', default=10,
        help='Display order on the booking form; lower numbers appear first.')
    active = fields.Boolean(
        string='Active', default=True,
        help='Uncheck to hide this service from the booking form without deleting it.')
    icon = fields.Char(
        string='Icon Class',
        default='fa-shield',
        help='FontAwesome class for the service icon, e.g. "fa-shield", "fa-car".'
    )
