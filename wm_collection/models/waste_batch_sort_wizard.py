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
from odoo.exceptions import UserError


class WasteBatchSortWizard(models.TransientModel):
    """Wizard to split a mixed-material waste batch into single-material child batches with stock moves."""
    _name = 'waste.batch.sort.wizard'
    _description = 'Sort Waste Batch'

    batch_id = fields.Many2one(
        'waste.batch',
        string='Batch',
        required=True,
        readonly=True,
        domain="[('is_received', '=', True)]",
    )
    source_location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        related='batch_id.location_id',
        readonly=True,
    )
    line_ids = fields.One2many(
        'waste.batch.sort.wizard.line',
        'wizard_id',
        string='Materials to Sort',
    )
    output_batch_mode = fields.Selection([
        ('per_material', 'Separate Batch per Material (1 batch per sorted line)'),
        ('consolidated', 'Single Consolidated Batch (All sorted lines in 1 batch)'),
    ], string='Output Batch Mode', default='per_material', required=True)
    notes = fields.Text(string='Sorting Notes')
    has_hazardous_lines = fields.Boolean(
        string='Contains Hazardous',
        compute='_compute_has_hazardous_lines',
        help='True when at least one material in the sort list is hazardous.',
    )

    @api.model
    def default_get(self, fields_list):
        """ Override default_get to provide dynamic default values."""
        res = super().default_get(fields_list)
        batch_id = self.env.context.get('default_batch_id')
        if not batch_id or 'line_ids' not in fields_list:
            return res

        batch = self.env['waste.batch'].browse(batch_id)

        if self.env.context.get('default_sort_by_category'):
            res['output_batch_mode'] = 'consolidated'
        elif self.env.context.get('default_sort_by_material'):
            res['output_batch_mode'] = 'per_material'

        material_config_model = self.env['wm.waste.material.sort.config']
        category_config_model = self.env['wm.waste.category.sort.config']

        line_cmds = []
        for bline in batch.line_ids.filtered(lambda l: l.remaining_qty > 0):
            category_config = None
            if batch.category_id:
                category_config = category_config_model.search(
                    [('category_id', '=', batch.category_id.id)], limit=1
                )
            if not category_config and bline.category_id:
                category_config = category_config_model.search(
                    [('category_id', '=', bline.category_id.id)], limit=1
                )

            material_config = material_config_model.search(
                [('material_id', '=', bline.material_id.id)], limit=1
            ) if bline.material_id else None

            dest_prod = getattr(material_config, 'dest_product_id', False) if material_config else False
            if not dest_prod:
                dest_prod = bline.product_id

            dest_loc = False
            if category_config and category_config.dest_location_id:
                dest_loc = category_config.dest_location_id
            elif material_config and material_config.dest_location_id:
                dest_loc = material_config.dest_location_id

            line_cmds.append((0, 0, {
                'batch_line_id': bline.id,
                'sort_qty': bline.remaining_qty,
                'dest_product_id': dest_prod.id if dest_prod else False,
                'dest_location_id': dest_loc.id if dest_loc else False,
            }))

        res['batch_id'] = batch.id
        res['line_ids'] = line_cmds
        return res

    @api.depends('line_ids.hazardous')
    def _compute_has_hazardous_lines(self):
        """
        Check whether any sort wizard lines contain a hazardous-classified
        waste material, surfacing a warning banner to remind operators of
        special handling protocols.
        """
        for wizard in self:
            wizard.has_hazardous_lines = any(wizard.line_ids.mapped('hazardous'))

    def action_autofill_remaining(self):
        """
        Auto-populate all sort wizard lines with their maximum sortable
        quantity (actual batch weight minus already sorted), allowing one-click
        full-sort confirmation.
        """
        self.ensure_one()
        for line in self.line_ids:
            line.sort_qty = line.remaining_qty
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_confirm_sort(self):
        """
        Validate sort line quantities against available batch weight, execute
        material segregation into child batches, and transition the parent
        batch to 'sorted' state.
        """
        self.ensure_one()
        if not self.env.user.has_group('wm_collection.group_wm_sorting_enabled'):
            raise UserError(_("Sorting is not enabled in settings."))
        self = self.with_context(default_batch_id=False)
        if not self.line_ids:
            raise UserError(_("There is nothing to sort."))

        active_lines = self.line_ids.filtered(lambda l: l.sort_qty > 0)
        if not active_lines:
            raise UserError(_(
                "Set a sort quantity greater than zero on at least one line."
            ))
        for line in active_lines:
            if not line.dest_product_id:
                line.dest_product_id = line.batch_line_id.product_id
            if not line.dest_location_id:
                raise UserError(_(
                    "Please select a destination location for %s."
                ) % line.material_id.display_name)

        child_batches = self.env['waste.batch']
        lines_data = [{
            'batch_line': l.batch_line_id,
            'sort_qty': l.sort_qty,
            'dest_product': l.dest_product_id or l.batch_line_id.product_id,
            'dest_location': l.dest_location_id,
        } for l in active_lines]

        if self.output_batch_mode == 'consolidated':
            child_batches |= self.batch_id._create_sorted_child_batch(
                lines_data=lines_data,
                dest_location=active_lines[0].dest_location_id,
                mode='consolidated',
            )
        else:  # per_material
            child_batches |= self.batch_id._create_sorted_child_batch(
                lines_data=lines_data,
                dest_location=active_lines[0].dest_location_id,
                mode='per_material',
            )

        if self.notes:
            self.batch_id.message_post(body=_(
                "Sorting notes: %s"
            ) % self.notes)

        action = {
            'name': _('Sorted Batches'),
            'type': 'ir.actions.act_window',
            'res_model': 'waste.batch',
            'view_mode': 'list,form',
            'domain': [('id', 'in', child_batches.ids)],
            'context': {'create': False},
        }
        if len(child_batches) == 1:
            action.update({'view_mode': 'form', 'res_id': child_batches.id})
        return action


class WasteBatchSortWizardLine(models.TransientModel):
    """Material segregation line in the sort wizard allocating weight to a child batch."""
    _name = 'waste.batch.sort.wizard.line'
    _description = 'Sort Waste Batch Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'waste.batch.sort.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(default=10)
    batch_line_id = fields.Many2one(
        'waste.batch.line',
        string='Source Line',
        required=True,
    )
    material_id = fields.Many2one(
        'product.template',
        string='Material',
        related='batch_line_id.material_id',
        readonly=True,
    )
    category_id = fields.Many2one(
        'wm.waste.category',
        string='Category',
        related='batch_line_id.category_id',
        readonly=True,
    )
    hazardous = fields.Boolean(
        string='Hazardous',
        related='batch_line_id.hazardous',
        readonly=True,
    )
    source_uom_id = fields.Many2one(
        'uom.uom',
        string='UoM',
        related='batch_line_id.uom_id',
        readonly=True,
    )
    remaining_qty = fields.Float(
        string='Available to Sort',
        related='batch_line_id.remaining_qty',
        readonly=True,
        digits=(16, 3),
    )
    sort_qty = fields.Float(
        string='Sort Qty',
        digits=(16, 3),
        required=True,
    )
    dest_product_id = fields.Many2one(
        'product.product',
        string='Destination Product',
        domain="[('type', '=', 'consu')]",
    )
    dest_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        domain="[('usage', '=', 'internal')]",
    )

    @api.onchange('material_id')
    def _onchange_material_id(self):
        """
        Auto-populate the sort destination location and expected tare weight
        when the operator selects a waste material product in the sort wizard line.
        """
        if not self.material_id:
            return
        config = self.env['wm.waste.material.sort.config'].search(
            [('material_id', '=', self.material_id.id)], limit=1
        )
        if config:
            self.dest_product_id = config.dest_product_id
            self.dest_location_id = config.dest_location_id

    @api.constrains('sort_qty')
    def _check_sort_qty(self):
        """
        Validate that the total sort quantity across all wizard lines does not
        exceed the available unsorted batch quantity, preventing
        over-allocation errors.
        """
        for line in self:
            if line.sort_qty < 0:
                raise UserError(_("Sort quantity cannot be negative."))
            if line.sort_qty - line.remaining_qty > 1e-6:
                raise UserError(_(
                    "Cannot sort %(qty)s of %(mat)s — only %(rem)s remains "
                    "unsorted on this batch line.",
                    qty=line.sort_qty,
                    mat=line.material_id.display_name,
                    rem=line.remaining_qty,
                ))
