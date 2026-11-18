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
from odoo import api, fields, models


class PropelleProject(models.Model):
    """New development sold for a developer."""
    _name = 'propelle.project'
    _description = 'Development Project'
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char(
        string='Project', required=True, translate=True,
        help='Name of the development.')
    location = fields.Char(
        string='Project Location', required=True,
        help='Area and city of the development, for example Bel Air, '
             'Los Angeles.')
    city_id = fields.Many2one(
        'propelle.city', string='Listing City', ondelete='set null',
        help='City whose homes for sale are linked from a completed project.')
    description = fields.Text(
        string='Project Description', translate=True,
        help='Short description shown in the project list.')
    state = fields.Selection(
        selection=[('selling', 'Now selling'), ('soon', 'Coming soon'),
                   ('completed', 'Completed')],
        string='Status', required=True, default='selling',
        help='Status used by the project filter of the website.')
    availability_label = fields.Char(
        string='Availability', translate=True,
        help='Label shown on the photo, for example 9 units left. Left empty, '
             'the status is shown.')
    availability_style = fields.Selection(
        string='Availability Badge Style',
        selection=[('open', 'Open'), ('limited', 'Limited'),
                   ('soon', 'Coming soon'), ('sold', 'Sold')],
        required=True, default='open',
        help='Colour of the availability label.')
    currency_id = fields.Many2one(
        'res.currency', string='Project Currency', required=True,
        default=lambda self: self.env.company.currency_id,
        help='Currency of the starting price.')
    price_from = fields.Monetary(
        string='Starting Price', currency_field='currency_id',
        help='Starting price of the homes of the project.')
    units_label = fields.Char(
        string='Units', translate=True,
        help='Number and kind of homes, for example 86 apartments.')
    completion_label = fields.Char(
        string='Completion', translate=True,
        help='Completion note, for example Completion 2026.')
    image_alt = fields.Char(
        string='Photo Description', translate=True,
        help='Short description of the photo, read by screen readers.')
    is_featured = fields.Boolean(
        string='Featured',
        help='Featured projects are shown in the showcase at the top of the '
             'Projects page.')
    sequence = fields.Integer(
        string='Display Order', default=10,
        help='Order of the project on the website.')
    is_published = fields.Boolean(
        string='Published', default=True, copy=False,
        help='Only published projects are shown on the website.')
    active = fields.Boolean(
        string='Active Project', default=True,
        help='Archived projects are hidden everywhere.')
    availability = fields.Char(
        string='Shown Availability', compute='_compute_availability',
        help='Availability label shown on the website.')
    price_label = fields.Char(
        string='Shown Price', compute='_compute_price_label',
        help='Starting price as shown on the website.')
    city_name = fields.Char(
        string='Project City', compute='_compute_city_name',
        help='City part of the location.')

    @api.depends('availability_label', 'state')
    def _compute_availability(self):
        """Use the availability label, or the name of the status."""
        labels = dict(self._fields['state']._description_selection(self.env))
        for record in self:
            record.availability = record.availability_label or labels.get(
                record.state, '')

    @api.depends('price_from', 'currency_id')
    def _compute_price_label(self):
        """Format the starting price in its short form."""
        for record in self:
            record.price_label = record.currency_id._propelle_format(
                record.price_from, compact=True)

    @api.depends('location')
    def _compute_city_name(self):
        """Keep the last part of the location, which is the city."""
        for record in self:
            record.city_name = (record.location or '').split(',')[-1].strip()

    def action_toggle_published(self):
        """Publish or unpublish the project on the website."""
        for record in self:
            record.is_published = not record.is_published
