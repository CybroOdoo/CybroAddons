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


class StockLot(models.Model):
    """Links batches to their reserve samples and offers the Retain Sample action."""
    _inherit = 'stock.lot'

    retention_sample_ids = fields.One2many('pharma.retention.sample', 'lot_id',
                                           string='Retention Samples',
                                           help='Reserve samples recorded for this batch.')
    retention_sample_count = fields.Integer(compute='_compute_retention_sample',
                                            help='Number of reserve samples of this batch.')
    show_retain_sample = fields.Boolean(compute='_compute_retention_sample',
                                        help='Released and no reserve sample created yet.')

    @api.depends('lot_status', 'retention_sample_ids')
    def _compute_retention_sample(self):
        """Count samples and decide whether the Retain Sample button shows."""
        for lot in self:
            lot.retention_sample_count = len(lot.retention_sample_ids)
            # Offered on every released batch; the product's retention rule
            # only decides whether a missing sample is chased.
            lot.show_retain_sample = bool(
                lot.lot_status == 'released' and not lot.retention_sample_ids)

    @api.model
    def _pharma_retention_missing_domain(self):
        """Released batches that carry a retention rule but no confirmed sample."""
        return [
            ('lot_status', '=', 'released'),
            ('product_id.retention_required', '=', True),
            ('retention_sample_ids', 'not any', [('state', '!=', 'draft')]),
        ]

    def action_create_retention_sample(self):
        """Create the batch's draft reserve sample; it is opened from the smart button."""
        self.ensure_one()
        self.env['pharma.retention.sample']._pharma_create_for_lot(self)
        return True

    def action_view_retention_samples(self):
        """Open this batch's reserve samples."""
        self.ensure_one()
        action = {
            'name': self.env._('Retention Samples'),
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.retention.sample',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
        }
        if len(self.retention_sample_ids) == 1:
            action.update(view_mode='form', res_id=self.retention_sample_ids.id)
        return action
