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

PROPERTY_TYPES = [
    ('villa', 'Villa'),
    ('apartment', 'Apartment'),
    ('house', 'Family home'),
    ('commercial', 'Commercial'),
]


class PropelleProperty(models.Model):
    """Home, apartment or office listed for sale or for rent."""
    _name = 'propelle.property'
    _description = 'Property Listing'
    _inherit = ['image.mixin']
    _order = 'sequence, date_listed desc, id desc'

    name = fields.Char(
        string='Title', required=True, translate=True,
        help='Name of the listing shown on the website.')
    listing_type = fields.Selection(
        string='Sale or Rent',
        selection=[('sale', 'For sale'), ('rent', 'For rent')],
        required=True, default='sale', index=True,
        help='Whether the property is listed on the Buy or on the Rent page.')
    property_type = fields.Selection(
        string='Kind of Property', selection=PROPERTY_TYPES, required=True,
        default='house',
        help='Type used by the property type filter of the website.')
    type_label = fields.Char(
        string='Tag', translate=True,
        help='Label shown on the photo of the listing, for example Penthouse '
             'or Loft. Left empty, the property type is shown.')
    city_id = fields.Many2one(
        'propelle.city', string='Property City', required=True,
        ondelete='restrict',
        help='City of the property, used by the location filter.')
    neighbourhood = fields.Char(
        string='Neighbourhood Name',
        help='Area of the city shown before the city name.')
    currency_id = fields.Many2one(
        'res.currency', string='Listing Currency', required=True,
        default=lambda self: self.env.company.currency_id,
        help='Currency of the price.')
    price = fields.Monetary(
        string='Asking Price', currency_field='currency_id',
        help='Asking price for a sale, or rent per month for a rental.')
    bedrooms = fields.Integer(
        string='Number of Bedrooms',
        help='Number of bedrooms. Leave 0 for an open plan space.')
    bathrooms = fields.Integer(
        string='Number of Bathrooms', help='Number of bathrooms.')
    area = fields.Integer(
        string='Area (sq ft)', help='Living or usable area in square feet.')
    is_furnished = fields.Boolean(
        string='Furnished',
        help='Whether the rental comes furnished.')
    image_alt = fields.Char(
        string='Photo Description', translate=True,
        help='Short description of the photo, read by screen readers.')
    date_listed = fields.Date(
        string='Listed On', default=fields.Date.context_today,
        help='Date the listing went live, used by the Newest sort.')
    sequence = fields.Integer(
        string='Display Order', default=10,
        help='Order of the listing on the website.')
    is_published = fields.Boolean(
        string='Published', default=True, copy=False,
        help='Only published listings are shown on the website.')
    active = fields.Boolean(
        string='Active Listing', default=True,
        help='Archived listings are hidden everywhere.')
    location = fields.Char(
        string='Location Summary', compute='_compute_location',
        help='Neighbourhood and city, as shown on the website.')
    tag = fields.Char(
        string='Shown Tag', compute='_compute_tag',
        help='Label shown on the photo of the listing.')
    price_label = fields.Char(
        string='Shown Price', compute='_compute_price_label',
        help='Price as shown on the website.')

    @api.depends('neighbourhood', 'city_id.name', 'city_id.state_code')
    def _compute_location(self):
        """Build the location line: neighbourhood, city and state code."""
        for record in self:
            record.location = ', '.join(part for part in (
                record.neighbourhood, record.city_id.name,
                record.city_id.state_code) if part)

    @api.depends('type_label', 'property_type')
    def _compute_tag(self):
        """Use the tag of the listing, or the name of its property type."""
        labels = dict(self._fields['property_type']._description_selection(
            self.env))
        for record in self:
            record.tag = record.type_label or labels.get(
                record.property_type, '')

    @api.depends('price', 'currency_id')
    def _compute_price_label(self):
        """Format the price without decimals, as in the listings."""
        for record in self:
            record.price_label = record.currency_id._propelle_format(
                record.price)

    def action_toggle_published(self):
        """Publish or unpublish the listing on the website."""
        for record in self:
            record.is_published = not record.is_published

    def _propelle_card_values(self):
        """Values of the listing used by the booking page.

        :return: dictionary with the id, status, title, location, price,
            type and photo URL of the listing.
        """
        self.ensure_one()
        price = self.price_label
        if self.listing_type == 'rent':
            price = self.env._('%(price)s / month', price=price)
        return {
            'id': str(self.id),
            'status': self.listing_type,
            'title': self.name,
            'loc': self.location,
            'price': price,
            'type': self.tag,
            'city': self.city_id.name,
            'img': '/web/image/propelle.property/{}/image_512'.format(self.id),
        }
