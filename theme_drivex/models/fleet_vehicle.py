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
from odoo.exceptions import ValidationError


class FleetVehicle(models.Model):
    """Fleet Vehicle Model Extension."""
    _inherit = 'fleet.vehicle'

    is_available_on_website = fields.Boolean(string="Published on Website",
                             help='Is this vehicle available on the website?')
    publish_on_homepage = fields.Boolean(
        string="Show on Homepage Premium Section",
        help='Show this vehicle on the homepage.')
    daily_rate = fields.Monetary(string="Daily Rental Rate",
                                 currency_field='currency_id',
                                 help='Cost per day to rent the vehicle.')

    currency_id = fields.Many2one('res.currency',
                                  related='company_id.currency_id',
                                  readonly=True, help='Currency.')

    website_description = fields.Html(string="Website Description",
                                      sanitize_attributes=False,
                                      help='Description shown on the website.')

    feature_ids = fields.Many2many(
        'fleet.vehicle.feature',
        string="Rental Features",
        help='Features of the vehicle.')
    vehicle_image_ids = fields.One2many(
        'fleet.vehicle.image', 'vehicle_id',
        string="Gallery Images",
        help='Images of the vehicle.')

    @api.constrains('publish_on_homepage')
    def _check_homepage_vehicles(self):
        """Limit homepage vehicles to 3."""
        for record in self:
            if record.publish_on_homepage:
                count = self.search_count([('publish_on_homepage', '=', True)])
                if count > 3:
                    raise ValidationError(
                        "You can only publish a maximum of 3 vehicles on "
                        "the homepage premium section. Please disable another vehicle first.")
