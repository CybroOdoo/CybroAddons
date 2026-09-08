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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WasteCategorySortConfig(models.Model):
    """Per-category default for the Sort Batch wizard."""
    _name = 'wm.waste.category.sort.config'
    _description = 'Waste Category Sort Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc, category_id'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference',
        required=True, copy=False, readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )

    active = fields.Boolean(default=True, tracking=True)
    category_id = fields.Many2one(
        'wm.waste.category',
        string='Waste Category',
        required=True,
        tracking=True,
    )
    dest_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=True,
        domain="[('usage', '=', 'internal')]",
        help='Where this category is stored once sorted.',
        tracking=True,
    )
    notes = fields.Char(string='Notes', tracking=True)

    _category_uniq = models.Constraint('UNIQUE(category_id)', 'A sort configuration already exists for this waste category.')

    @api.constrains('category_id')
    def _check_unique_category(self):
        """
        Ensure that each waste category has only one sorting configuration
        record, preventing conflicting sorting rules for the same material
        stream.
        """
        for record in self:
            if record.category_id:
                count = self.search_count([('category_id', '=', record.category_id.id)])
                if count > 1:
                    raise ValidationError(_("A sort configuration already exists for this waste category!"))

    @api.model_create_multi
    def create(self, vals_list):
        """ Override create to implement custom initialization and validation logic. """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.waste.category.sort.config') or _('New')
        return super().create(vals_list)
