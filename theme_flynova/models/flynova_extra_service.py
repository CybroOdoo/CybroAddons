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
    """Flynova Extra Service"""
    _name = 'flynova.extra.service'
    _description = 'Flynova Extra Service'
    _order = 'sequence, name'

    name = fields.Char(string='Service Name', required=True,
                       help='The display name of the extra service shown to customers during booking.')
    description = fields.Char(string='Short Description',
                              help='A brief one-line description shown alongside the service name on the booking form.')
    price = fields.Float(string='Price', required=True, digits=(10, 2),
                         help='The cost of this extra service per booking. Added to the order total when selected.')
    sequence = fields.Integer(string='Sequence', default=10,
                              help='Determines the display order of services. Lower values appear first.')
    active = fields.Boolean(string='Active', default=True,
                            help='Uncheck to hide this service from the booking form without deleting it.')
    icon = fields.Char(
        string='Icon Class',
        default='fa-shield',
        help='FontAwesome icon class, e.g. fa-shield, fa-heartbeat'
    )
