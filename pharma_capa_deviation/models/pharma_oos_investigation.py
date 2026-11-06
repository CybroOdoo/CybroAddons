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
from odoo import models


class PharmaOosInvestigation(models.Model):
    """Raise a deviation when an OOS investigation closes with a reject disposition."""
    _inherit = 'pharma.oos.investigation'

    def _create_oos_deviation(self):
        """Raise a critical QC deviation for a rejected OOS investigation."""
        for rec in self:
            # Raised when QA closes the investigation with a reject; QA has no
            # create right on deviations, so it is created elevated (the same
            # as the CAPA auto-raised by a deviation investigation).
            self.env['pharma.deviation'].sudo().create({
                'stage': 'qc',
                'classification': 'critical',
                'description': self.env._(
                    "OOS Failure — Parameter: %(parameter)s | Expected: %(min)s - %(max)s"
                    " | Actual: %(actual)s | Batch: %(batch)s",
                    parameter=rec.result_line_id.parameter,
                    min=rec.result_line_id.expected_min,
                    max=rec.result_line_id.expected_max,
                    actual=rec.result_line_id.actual_value or '—',
                    batch=rec.result_line_id.test_order_id.lot_id.name,
                ),
                'immediate_action': self.env._(
                    "OOS investigation %(oos)s confirmed failure. Conclusion: %(conclusion)s",
                    oos=rec.name, conclusion=rec.conclusion or ''),
                'oos_investigation_id': rec.id,
                'qc_result_id': rec.result_line_id.id,
                'lot_id': rec.result_line_id.test_order_id.lot_id.id,
            })
