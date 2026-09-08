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


class WasteBatch(models.Model):
    """Extends Waste Batch with recycling order linkage and recovery tracking."""
    _inherit = 'waste.batch'

    recycling_order_ids = fields.One2many(
        'recycling.order',
        'waste_batch_id',
        string='Recycling Orders',
    )
    recycling_order_count = fields.Integer(
        string='Recycling Orders',
        compute='_compute_recycling_order_count',
        store=True,
    )

    @api.depends('recycling_order_ids')
    def _compute_recycling_order_count(self):
        """
        Compute the total number of associated recycling order records linked
        to this WasteBatch to update smart buttons and summary badges.
        """
        for batch in self:
            batch.recycling_order_count = len(batch.recycling_order_ids)

    def action_view_recycling_orders(self):
        """
        Open the list of recycling orders created from this sorted waste batch,
        allowing recycling supervisors to monitor processing progress and yield
        results.
        """
        self.ensure_one()
        return {
            'name': _('Recycling Orders — %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'recycling.order',
            'view_mode': 'list,form',
            'domain': [('waste_batch_id', '=', self.id)],
            'context': {
                'default_waste_batch_id': self.id,
            },
        }

    def action_create_recycling_order(self):
        """
        Quick-create a recycling order pre-filled from this batch.
        """
        self.ensure_one()
        from odoo.exceptions import UserError

        if not self.is_received:
            raise UserError(
                _("The batch must be received into stock before creating a recycling order.")
            )

        if self.recycling_order_ids:
            raise UserError(
                _("A recycling order already exists for this batch (%s). "
                  "Only one recycling order is allowed per waste batch.") % self.name
            )

        if self.has_multiple_materials:
            raise UserError(
                _("Recycling orders can only be created for batches with a single line or the same waste material across all lines.")
            )

        return {
            'name': _('New Recycling Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'recycling.order',
            'view_mode': 'form',
            'context': {
                'default_waste_batch_id': self.id,
            },
        }
