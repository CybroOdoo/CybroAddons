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

from ..models.pharma_retention_sample import INTERNAL_CTX


class PharmaRetentionDisposalWizard(models.TransientModel):
    """Records the approved disposal of a reserve sample (quality management only)."""
    _name = 'pharma.retention.disposal.wizard'
    _description = 'Dispose Retention Sample'
    _inherit = ['pharma.workflow.mixin']

    sample_id = fields.Many2one('pharma.retention.sample', string='Retention Sample',
                                required=True, readonly=True,
                                help='Reserve sample being disposed of.')
    disposal_due_date = fields.Date(related='sample_id.disposal_due_date',
                                    help='Date the retention period expired.')
    remaining_qty = fields.Float(related='sample_id.remaining_qty',
                                 help='Quantity being destroyed.')
    product_uom_id = fields.Many2one(related='sample_id.product_uom_id',
                                     help='Unit of measure of the quantity.')
    disposal_method = fields.Selection(
        selection=lambda self: self.env['pharma.retention.sample']._fields['disposal_method'].selection,
        required=True, help='How the sample is destroyed.')
    disposal_reference = fields.Char(help='Destruction certificate or waste note number.')
    disposal_note = fields.Text(string='Remarks', required=True,
                                help='Remarks recorded with the disposal.')

    def action_confirm(self):
        """Mark the sample disposed on the register; the record itself stays."""
        self.ensure_one()
        self._check_pharma_group('pharmaceutical_base.group_pharma_role_qa',
                                 self.env._("Only quality management can dispose of a retention sample."))
        sample = self.sample_id
        if sample.state != 'retained':
            raise UserError(self.env._("%s is already disposed.", sample.name))
        if not sample.is_disposal_due:
            raise UserError(self.env._(
                "The retention period of %(ref)s has not expired (due %(due)s).",
                ref=sample.name, due=sample.disposal_due_date or self.env._('— no batch expiry set')))
        sample.with_context(**{INTERNAL_CTX: True}).write({
            'state': 'disposed',
            'disposed_by': self.env.user.id,
            'disposed_on': fields.Datetime.now(),
            'disposal_method': self.disposal_method,
            'disposal_reference': self.disposal_reference,
            'disposal_note': self.disposal_note,
        })
        sample.message_post(body=self.env._(
            "Disposal approved and recorded by %(user)s (%(qty)s %(uom)s destroyed).",
            user=self.env.user.name, qty=sample.remaining_qty, uom=sample.product_uom_id.name))
        return {'type': 'ir.actions.act_window_close'}
