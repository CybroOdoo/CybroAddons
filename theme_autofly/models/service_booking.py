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
from odoo import api, fields, models, _


class ServiceBooking(models.Model):
    """This model is used managing service booking details."""
    _name = "service.booking"
    _description = "Website Car Service Booking"

    reference = fields.Char(string="Reference", readonly=True,
                            help="Booking sequence")
    state = fields.Selection(
        [('draft', 'Draft'), ('running', 'Running'),
         ('cancel', 'Cancel'), ('done', 'Done')], string="State")
    name = fields.Char('Name', required=True, help="Name of the service")
    email = fields.Char(string='Email', help="Email address")
    description = fields.Char(string='Description',
                              help="Add if you have any description")

    @api.model_create_multi
    def create(self, vals):
        """Supering create function for generating sequence."""
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code(
                'reference.sequence') or _('New')
        return super(ServiceBooking, self).create(vals)
