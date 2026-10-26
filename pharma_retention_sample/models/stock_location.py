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


class StockLocation(models.Model):
    """Marks internal locations used to hold reserve samples.

    Samples are only recorded against these locations; no quant is ever
    created for them, so they stay out of on-hand and valuation reports.
    """
    _inherit = 'stock.location'

    pharma_is_retention_location = fields.Boolean(
        string='Retention Sample Location',
        help='Offer this location for reserve samples. Samples are recorded '
             'here but are not held as stock.',
    )
    retention_sample_ids = fields.One2many('pharma.retention.sample', 'location_id',
                                           string='Retention Samples',
                                           help='Reserve samples recorded at this location.')
    retention_sample_count = fields.Integer(compute='_compute_retention_sample_count',
                                            string='Samples Held',
                                            help='Reserve samples currently held here.')

    def _compute_retention_sample_count(self):
        """Count the retained (not disposed) samples at each location."""
        counts = dict(self.env['pharma.retention.sample']._read_group(
            [('location_id', 'in', self.ids), ('state', '=', 'retained')],
            ['location_id'], ['__count']))
        for location in self:
            location.retention_sample_count = counts.get(location, 0)

    @api.constrains('pharma_is_retention_location', 'usage')
    def _check_pharma_retention_location(self):
        """Only internal locations can hold reserve samples."""
        for location in self:
            if location.pharma_is_retention_location and location.usage != 'internal':
                raise ValidationError(self.env._(
                    "A retention sample location must be an internal location."))

    def action_view_retention_samples(self):
        """Open the reserve samples held at this location."""
        self.ensure_one()
        return {
            'name': self.env._('Retention Samples'),
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.retention.sample',
            'view_mode': 'list,form',
            'domain': [('location_id', '=', self.id)],
            'context': {'search_default_filter_retained': 1},
        }
