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
from odoo.exceptions import ValidationError
from odoo.tools.translate import _



class MrpProduction(models.Model):
    """
    Extends mrp.production to add inspection functionality.
    Key behaviour:
    ──────────────
    1.  After the MO reaches state='done', an "Inspect" button appears in the header.
    2.  Clicking it calls action_create_inspection() which:
          a. Finds all active Inspection Points that match the MO's product / category.
          b. Creates one Inspection Order per matching point, pre-filled with checklist lines.
          c. Immediately starts each order (state → in_progress).
          d. Returns the first Inspection Order form so the inspector can fill it right away
             (same UX as Odoo Quality's "Register Quality Check").
    3.  The smart button shows how many inspections exist and their overall state.
    4.  The "Inspect" button appears when:
          - The MO is done  (state == 'done')
          - (Note: The Inspection & Checklist module must be enabled in settings)
    """
    _inherit = 'mrp.production'

    inspection_ids = fields.One2many(
        'oil.inspection.order',
        'production_id',
        string='Inspection Orders',
        help="Lists the inspection Orders.")
    inspection_count = fields.Integer(
        string='Inspections',
        compute='_compute_inspection_count',
        help="Enter the inspections.")
    inspection_state = fields.Selection(
        [
            ('none', 'No Inspection'),
            ('pending', 'Pending'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
        ],
        string='Inspection Status',
        compute='_compute_inspection_state',
        store=True,
        help="Choose the inspection Status.")

    # ─── Computed fields ───────────────────────────────────────────────────────

    @api.depends('inspection_ids')
    def _compute_inspection_count(self):
        """
        Computes the number of inspection orders linked to this manufacturing order.
        """
        for rec in self:
            rec.inspection_count = len(rec.inspection_ids)

    @api.depends('inspection_ids.state')
    def _compute_inspection_state(self):
        """Set the overall inspection status for each production order."""
        for rec in self:
            inspections = rec.inspection_ids
            if not inspections:
                rec.inspection_state = 'none'
            elif any(i.state == 'failed' for i in inspections):
                rec.inspection_state = 'failed'
            elif all(i.state == 'passed' for i in inspections):
                rec.inspection_state = 'passed'
            else:
                rec.inspection_state = 'pending'

    # ─── Actions ──────────────────────────────────────────────────────────────

    def action_create_inspection(self):
        """
        Called when the user clicks the 'Inspect' button on a done MO.
        Finds matching Inspection Points, creates Inspection Orders,
        then opens the first one so the inspector can start immediately.
        This mirrors Odoo Quality's 'Register Quality Check' pattern.
        """
        self.ensure_one()

        # Find Inspection Points that match this product
        all_points = self.env['oil.inspection.point'].search(
            [('active', '=', True)])
        matching_points = all_points.filtered(
            lambda p: p.matches_product(self.product_id))

        if not matching_points:
            raise ValidationError(
                _('No active Quality Points found for product "%s". '
                  'Please configure one under Oil ERP → Configuration → Quality Points.')
                % self.product_id.display_name)

        created_orders = self.env['oil.inspection.order']
        for point in matching_points:
            order = self.env['oil.inspection.order'].create({
                'production_id': self.id,
                'inspection_point_id': point.id,
                'responsible_id': point.responsible_id.id if point.responsible_id
                else self.env.user.id,
                'line_ids': [
                    (0, 0, {
                        'name': criteria.name,
                        'guideline': criteria.guideline,
                        'is_critical': criteria.is_critical,
                        'sequence': criteria.sequence,
                        'evaluation_type': criteria.evaluation_type,
                        'target_value': criteria.target_value,
                    })
                    for criteria in point.criteria_ids
                ],
            })
            order.action_start()
            created_orders |= order

        # Open the first inspection order form
        if len(created_orders) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Inspection'),
                'res_model': 'oil.inspection.order',
                'res_id': created_orders.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Inspections'),
                'res_model': 'oil.inspection.order',
                'view_mode': 'list,form',
                'domain': [('production_id', '=', self.id)],
                'context': {'default_production_id': self.id},
            }

    def action_view_inspections(self):
        """Open all Inspection Orders for this MO (smart button)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Inspections'),
            'res_model': 'oil.inspection.order',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.id)],
            'context': {'default_production_id': self.id},
        }
