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
from odoo import _, api, fields, models


class ServiceBooking(models.Model):
    """This model is used managing service booking details."""
    _name = "service.booking"
    _description = "Website Car Service Booking"

    name = fields.Char(required=True, help="Name of the service")
    reference = fields.Char(readonly=True, help="Booking sequence")
    state = fields.Selection([('draft', 'Draft'), ('running', 'Running'),
                              ('cancel', 'Cancel'), ('done', 'Done')])
    email = fields.Char(help="Email address")
    description = fields.Char(help="Add if you have any description")

    @api.model_create_multi
    def create(self, vals_list):
        """Supering create function for generating sequence."""
        for vals in vals_list:
            if vals.get('reference', _('New')) == _('New'):
                vals['reference'] = self.env['ir.sequence'].next_by_code(
                    'reference.sequence') or _('New')
            return super().create(vals)
