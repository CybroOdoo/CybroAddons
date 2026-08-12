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
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class PharmaQcTestOrder(models.Model):
    """Adds deviation/CAPA links and the deviation-closed approval gate to QC test orders."""
    _inherit = 'pharma.qc.test.order'

    deviation_ids = fields.Many2many(help='Specifies the Deviation Ids for this record.',
        comodel_name='pharma.deviation',
        compute='_compute_deviations_capas',
        string='Deviations',
    )

    capa_ids = fields.Many2many(help='Specifies the Capa Ids for this record.',
        comodel_name='pharma.capa',
        compute='_compute_deviations_capas',
        string='CAPAs',
    )

    def _compute_deviations_capas(self):
        """Executes the _compute_deviations_capas operation."""
        for order in self:
            deviations = self.env['pharma.deviation'].search([
                ('oos_investigation_id.result_line_id.test_order_id', '=', order.id)
            ])
            order.deviation_ids = deviations
            order.capa_ids = deviations.mapped('capa_ids')

    deviation_count = fields.Integer(
        string='Deviations',
        compute='_compute_deviation_count',
        help='Specifies the Deviations for this record related to OOS.'
    )

    def _compute_deviation_count(self):
        """Count the Deviations from this test order's OOS investigations."""
        for order in self:
            order.deviation_count = self.env['pharma.deviation'].search_count([
                ('oos_investigation_id.result_line_id.test_order_id', '=', order.id)
            ])

    def action_view_deviations(self):
        """Open all Deviations related to this test order."""
        self.ensure_one()
        return {
            'name': 'Deviations',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'pharma.deviation',
            'domain': [('oos_investigation_id.result_line_id.test_order_id', '=', self.id)],
            'context': {},
        }

    def _pharma_rejection_deferred(self):
        """Hold the segregation move while an open deviation owns the batch decision."""
        # With CAPA & Deviation management installed a QC failure only *opens*
        # the investigation: the material is moved to the Rejected location when
        # QA closes the deviation on a 'Reject' disposition (see
        # pharma.deviation.action_close). A failed test order with no open
        # deviation has no downstream decision to wait for, so it segregates
        # right away as in core.
        self.ensure_one()
        return bool(self.env['pharma.deviation'].sudo().search_count([
            ('oos_investigation_id.result_line_id.test_order_id', '=', self.id),
            ('status', '!=', 'closed'),
        ]))

    def _check_qc_deviations_closed(self):
        """Block approval while any deviation from this order's OOS investigations is open."""
        for rec in self:
            investigations = self.env['pharma.oos.investigation'].search([
                ('result_line_id', 'in', rec.result_line_ids.ids)
            ])
            if investigations:
                open_devs = self.env['pharma.deviation'].search([
                    ('oos_investigation_id', 'in', investigations.ids),
                    ('status', '!=', 'closed')
                ])
                if open_devs:
                    raise ValidationError(_(
                        "Cannot approve a test order with open related deviations. "
                        "Close the deviations and CAPAs first."))
