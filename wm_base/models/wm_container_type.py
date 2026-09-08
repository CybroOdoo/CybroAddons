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
from odoo import fields, models


class WmContainerType(models.Model):
    """Master data model for waste collection container types and tare weight definitions."""
    _name = 'wm.container.type'
    _description = 'Container Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Name', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    capacity_volume = fields.Float(
        string='Volume Capacity (L)',
        default=0.0,
        help='Volume capacity of the container in Litres (L).',
    )
    capacity = fields.Float(
        string='Capacity (L)',
        related='capacity_volume',
        readonly=False,
        store=True,
        help='Volume capacity of the container in Litres (L).',
    )
    capacity_weight = fields.Float(
        string='Max Payload Capacity (kg)',
        default=0.0,
        help='Maximum weight of waste the container is rated to safely hold in kg.',
    )
    default_tare_weight = fields.Float(
        string='Default Tare Weight (kg)',
        default=0.0,
        digits=(16, 3),
        help='Tare weight of the empty container unit in kg. Auto-filled on waste batches.',
    )
    category_ids = fields.Many2many(
        'wm.waste.category',
        relation='wm_container_type_waste_category_rel',
        column1='container_type_id',
        column2='category_id',
        string='Applicable Waste Categories',
        help='Waste categories this container type is approved to hold.',
    )
    compatible_category_ids = fields.Many2many(
        'wm.waste.category',
        compute='_compute_compatible_category_ids',
        inverse='_inverse_compatible_category_ids',
        string='Compatible Categories',
        help='Alias for applicable waste categories.',
    )
    is_hazardous_suitable = fields.Boolean(
        string='Suitable for Hazardous Waste',
        default=False,
        help='When checked, this container type will appear in the filtered dropdown for hazardous waste batches.',
    )
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')

    def _compute_compatible_category_ids(self):
        """Compute compatible category IDs by syncing from category_ids."""
        for rec in self:
            rec.compatible_category_ids = rec.category_ids

    def _inverse_compatible_category_ids(self):
        """Inverse handler to sync compatible_category_ids back to category_ids."""
        for rec in self:
            rec.category_ids = rec.compatible_category_ids
