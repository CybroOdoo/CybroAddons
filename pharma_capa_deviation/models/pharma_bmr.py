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
from odoo.exceptions import UserError
from odoo.tools.translate import _


class PharmaBmr(models.Model):
    """Adds deviation/CAPA gating to the BMR workflow."""
    _inherit = 'pharma.bmr'

    deviation_count = fields.Integer(
        compute='_compute_deviation_count',
        help='Specifies the Deviation Count for this record.',
    )

    def _compute_deviation_count(self):
        """Count the deviations linked to this BMR and its IPQC results."""
        for rec in self:
            if rec.production_id:
                devs = self.env['pharma.deviation'].search([
                    '|',
                    ('batch_id', '=', rec.production_id.id),
                    ('id', 'in', rec.ipqc_ids.mapped('deviation_id').ids)
                ])
                rec.deviation_count = len(devs)
            else:
                rec.deviation_count = 0

    def action_view_deviations(self):
        """Returns a window action to display all deviations associated with this BMR."""
        self.ensure_one()
        devs = self.env['pharma.deviation'].search([
            '|',
            ('batch_id', '=', self.production_id.id),
            ('id', 'in', self.ipqc_ids.mapped('deviation_id').ids)
        ])
        action = self.env["ir.actions.actions"]._for_xml_id("pharma_capa_deviation.pharma_deviation_action")
        if len(devs) == 1:
            action['views'] = [(self.env.ref('pharma_capa_deviation.pharma_deviation_form').id, 'form')]
            action['res_id'] = devs.id
        else:
            action['domain'] = [('id', 'in', devs.ids)]
        return action

    def _check_open_deviations_capas(self):
        """Block resume while the batch has open deviations or CAPAs."""
        for rec in self:
            open_deviations = self.env['pharma.deviation'].search([
                ('batch_id', '=', rec.production_id.id),
                ('status', '!=', 'closed')
            ])
            if open_deviations:
                raise UserError(_('Cannot resume — there are open Deviations:\n%s') % ', '.join(open_deviations.mapped('name')))

            open_capas = self.env['pharma.capa'].search([
                ('deviation_id.batch_id', '=', rec.production_id.id),
                ('status', '!=', 'closed')
            ])
            if open_capas:
                raise UserError(_('Cannot resume — there are open CAPAs:\n%s') % ', '.join(open_capas.mapped('name')))

    def _check_ipqc_failure_deviations(self):
        """Require every failed IPQC check to have a linked, closed deviation."""
        for rec in self:
            failed_ipqc = rec.ipqc_ids.filtered(lambda r: r.result == 'fail')
            for check in failed_ipqc:
                dev = check.deviation_id
                if not dev:
                    raise UserError(_(
                        'IPQC check "%s" failed but has no linked deviation. '
                        'Please raise a deviation first.'
                    ) % check.parameter)
                if dev.status != 'closed':
                    raise UserError(_(
                        'IPQC failure on "%s" has an open deviation (%s). '
                        'Close the deviation before completing the BMR.'
                    ) % (check.parameter, dev.name))
