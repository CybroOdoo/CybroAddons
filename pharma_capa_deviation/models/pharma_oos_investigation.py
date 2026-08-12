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
            self.env['pharma.deviation'].create({
                'stage': 'qc',
                'classification': 'critical',
                'description': f"OOS Failure — Parameter: {rec.result_line_id.parameter} | Expected: {rec.result_line_id.expected_min} - {rec.result_line_id.expected_max} | Actual: {rec.result_line_id.actual_value or '—'} | Batch: {rec.result_line_id.test_order_id.lot_id.name}",
                'immediate_action': f"OOS investigation {rec.name} confirmed failure. Conclusion: {rec.conclusion or ''}",
                'oos_investigation_id': rec.id,
                'qc_result_id': rec.result_line_id.id,
                'lot_id': rec.result_line_id.test_order_id.lot_id.id,
            })
