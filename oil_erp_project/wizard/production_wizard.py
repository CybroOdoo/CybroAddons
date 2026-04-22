# -*- coding: utf-8 -*-
#############################################################################
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
from odoo.tools.translate import _
from odoo.exceptions import UserError


class ProductionWizard(models.TransientModel):
    """Records production and creates the related stock transfer."""
    _name = 'production.wizard'
    _description = 'Production Wizard'

    task_id = fields.Many2one(
        'project.task',
        string='Well / Task',
        required=True,
        readonly=True,
        help="Select the well or Task.")
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        related='task_id.project_id',
        readonly=True,
        help="Select the project.")
    production_date = fields.Date(
        string='Production Date',
        required=True,
        default=fields.Date.context_today,
        help="Select the date for production Date.")
    storage_location_id = fields.Many2one(
        'stock.location',
        string='Storage Location',
        required=True,
        domain="[('usage', '=', 'internal')]",
        help='Location where the produced products will be stored.',)
    line_ids = fields.One2many(
        'production.wizard.line',
        'wizard_id',
        string='Production Lines',
        help="Lists the production Lines.")

    @api.model
    def default_get(self, fields_list):
        """Load the active task and default storage location."""
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            task = self.env['project.task'].browse(active_id)
            res['task_id'] = task.id
            if task.project_id and task.project_id.storage_location_id:
                res[
                    'storage_location_id'] = task.project_id.storage_location_id.id
        return res

    def action_confirm(self):
        """Create and validate the stock picking for produced items."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Please add at least one production line.'))
        if not self.storage_location_id:
            raise UserError(_('Please select a storage location.'))

        # Create stock picking to move products into the storage location
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not picking_type:
            raise UserError(
                _('No incoming picking type found for the current company.'))

        source_location = self.env.ref('stock.stock_location_suppliers')

        move_vals = []
        for line in self.line_ids:
            move_vals.append({
                'product_id': line.product_id.id,
                'product_uom_qty': line.produced_qty,
                'product_uom': line.uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': self.storage_location_id.id,
            })

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': self.storage_location_id.id,
            'origin': _('Production - %s', self.task_id.display_name),
            'scheduled_date': self.production_date,
            'move_ids': [(0, 0, vals) for vals in move_vals],
        })
        picking.action_confirm()
        picking.button_validate()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Production Recorded'),
                'message': _('Products have been stored in %s.',
                             self.storage_location_id.display_name),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }


class ProductionWizardLine(models.TransientModel):
    """Stores product lines entered in the production wizard."""
    _name = 'production.wizard.line'
    _description = 'Production Wizard Line'

    wizard_id = fields.Many2one(
        'production.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
        help="Select the wizard.")
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        help="Select the product.")
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True,
        help="Select the unit of Measure.")
    produced_qty = fields.Float(
        string='Produced Qty',
        required=True,
        default=1.0,
        help="Enter the produced Qty.")
    rate = fields.Float(
        string='Rate',
        help='Production rate.',)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set the unit of measure from the selected product."""
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id
