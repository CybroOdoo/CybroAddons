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


class WasteMaterialSortConfig(models.Model):
    """Per-material sorting default: defines the recycling method and destination location for the sort wizard."""
    _name = 'wm.waste.material.sort.config'
    _description = 'Waste Material Sort Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc, material_id'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference',
        required=True, copy=False, readonly=True,
        default=lambda self: _('New'),
        tracking=True,
    )

    active = fields.Boolean(default=True, tracking=True)
    material_id = fields.Many2one(
        'product.template',
        string='Waste Material',
        required=True,
        tracking=True,
        domain="[('is_waste_material', '=', True)]",
    )
    category_id = fields.Many2one(
        'wm.waste.category',
        string='Category',
        related='material_id.wm_waste_category_id',
        store=True,
        readonly=True,
    )
    dest_product_id = fields.Many2one(
        'product.product',
        string='Sorted Product',
        required=True,
        domain="[('type', '=', 'consu')]",
        help='The product used to represent this material in stock once '
             'it has been sorted out of a mixed batch.',
        tracking=True,
    )
    dest_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=True,
        domain="[('usage', '=', 'internal')]",
        help='Where this material is stored once sorted, based on its '
             'recycling method (e.g. a dedicated location per stream).',
        tracking=True,
    )
    notes = fields.Char(string='Notes', tracking=True)

    _material_uniq = models.Constraint('UNIQUE(material_id)', 'A sort configuration already exists for this waste material.')

    @api.onchange('material_id')
    def _onchange_material_id(self):
        """
        Clear the category field and reload sort destination location when the
        material product changes, ensuring the configuration remains consistent
        with the selected material.
        """
        if self.material_id and not self.dest_product_id:
            self.dest_product_id = False

    @api.constrains('material_id')
    def _check_unique_material(self):
        """
        Prevent duplicate sort configuration records for the same waste
        material product, ensuring each material has exactly one set of sorting
        rules and destination locations.
        """
        for record in self:
            if record.material_id:
                count = self.search_count([('material_id', '=', record.material_id.id)])
                if count > 1:
                    raise ValidationError(_("A sort configuration already exists for this waste material! Please edit the existing one instead of creating a new one."))

    @api.model_create_multi
    def create(self, vals_list):
        """ Override create to implement custom initialization and validation logic. """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.waste.material.sort.config') or _('New')
        return super().create(vals_list)
