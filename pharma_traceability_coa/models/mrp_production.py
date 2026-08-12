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
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    """Adds the QA Release step on top of the core batch-ready workflow."""
    _inherit = ['mrp.production', 'pharma.workflow.mixin']

    def action_qa_release(self):
        """Send a ready batch to the QA Release Queue."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            "Only QA can release a batch for QA.",
        )
        for bmr in self:
            if not bmr.qa_release_eligible:
                raise ValidationError("This batch is not ready for QA Release. Please ensure it "
                                      "is completed, the BMR is complete and finished-goods QC has passed.")

            # Prevent multiple QA release records
            existing_qa_release = self.env['pharma.qa.release'].search([('production_id', '=', bmr.id)], limit=1)
            if existing_qa_release:
                raise ValidationError("A QA Release Queue record already exists for this batch.")

            existing_coa = self.env['pharma.coa'].search([('batch_id', '=', bmr.id)], limit=1)
            if existing_coa:
                raise ValidationError("A Certificate of Analysis already exists for this batch.")

            # Strict compliance validation
            lot_ids = self.env['stock.lot']
            if bmr.lot_producing_ids:
                lot_ids |= bmr.lot_producing_ids
            lot_ids |= bmr.move_raw_ids.mapped('move_line_ids.lot_id')

            qc_tests = self.env['pharma.qc.test.order'].search([
                ('lot_id', 'in', lot_ids.ids)
            ])
            if not qc_tests or not all(t.status == 'passed' for t in qc_tests):
                raise ValidationError("All QC Test Orders for the produced lots must be passed before QA Release.")

            open_oos = self.env['pharma.oos.investigation'].search_count([
                ('result_line_id.test_order_id', 'in', qc_tests.ids),
                ('closed_on', '=', False)
            ])
            if open_oos > 0:
                raise ValidationError("There are open OOS investigations for this batch. They must be "
                                      "closed before QA Release.")

            # Deviation gate — only enforced when the optional pharma_capa_deviation
            # module is installed (no deviations exist otherwise).
            if 'pharma.deviation' in self.env:
                open_deviations = self.env['pharma.deviation'].search_count([
                    ('batch_id', '=', bmr.id),
                    ('status', 'in', ('open', 'under_investigation'))
                ])
                if open_deviations > 0:
                    raise ValidationError("There are open or under investigation deviations for this batch."
                                          " They must be resolved before QA Release.")

            # QA is a no-create role; the QA-release record is a downstream
            # artefact of the release action, so it is created with elevated
            # rights on QA's behalf.
            qa_release = self.env['pharma.qa.release'].sudo().create({
                'production_id': bmr.id,
                'lot_id': bmr.lot_producing_ids[0].id if bmr.lot_producing_ids else False,
            })

            # Post a message to BMR
            bmr.message_post(body=f"Sent to QA Release Queue: {qa_release.name}.")
