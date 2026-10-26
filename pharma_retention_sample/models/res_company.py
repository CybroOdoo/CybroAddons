# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    """Adds the default reserve-sample location to the company."""
    _inherit = 'res.company'

    pharma_retention_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Default Retention Location',
        domain="[('usage', '=', 'internal'), ('pharma_is_retention_location', '=', True)]",
        help='Internal location proposed for reserve samples when the product '
             'sets none. Samples are only recorded there, never held as stock.',
    )

    @api.constrains('pharma_retention_location_id')
    def _check_pharma_retention_location(self):
        """The default retention location must be marked as a retention location."""
        for company in self:
            location = company.pharma_retention_location_id
            if location and not location.pharma_is_retention_location:
                raise ValidationError(self.env._(
                    "The Default Retention Location must be marked as a retention "
                    "sample location."))

    @api.model
    def _pharma_create_retention_locations(self):
        """Give each company without a default a "Retention Samples" location.

        Created beside WH/Stock (under the warehouse view location), not inside
        it, so stock rules never reserve from it.
        """
        Location = self.env['stock.location'].sudo()
        configured = self.sudo().search([('pharma_retention_location_id', '!=', False)])
        configured.pharma_retention_location_id.pharma_is_retention_location = True
        for company in self.sudo().search([('pharma_retention_location_id', '=', False)]):
            warehouse = self.env['stock.warehouse'].sudo().search(
                [('company_id', '=', company.id)], limit=1)
            if not warehouse:
                continue
            location = Location.search([
                ('name', '=', 'Retention Samples'),
                ('location_id', '=', warehouse.view_location_id.id),
            ], limit=1) or Location.create({
                'name': 'Retention Samples',
                'usage': 'internal',
                'location_id': warehouse.view_location_id.id,
                'company_id': company.id,
                'pharma_is_retention_location': True,
            })
            location.pharma_is_retention_location = True
            company.pharma_retention_location_id = location
