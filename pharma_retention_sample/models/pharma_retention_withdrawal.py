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
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class PharmaRetentionWithdrawal(models.Model):
    """One quantity taken from a reserve sample. Entries are never edited or deleted."""
    _name = 'pharma.retention.withdrawal'
    _description = 'Retention Sample Withdrawal'
    _order = 'date desc, id desc'

    sample_id = fields.Many2one('pharma.retention.sample', string='Retention Sample',
                                required=True, index=True, ondelete='restrict',
                                domain=[('state', '=', 'retained')],
                                help='Reserve sample the quantity was taken from.')
    lot_id = fields.Many2one(related='sample_id.lot_id', store=True, string='Batch',
                             help='Batch of the reserve sample.')
    product_uom_id = fields.Many2one(related='sample_id.product_uom_id', string='Unit',
                                     help='Unit of measure of the quantity.')
    company_id = fields.Many2one(related='sample_id.company_id', store=True,
                                 help='Company holding the sample.')
    remaining_qty = fields.Float(related='sample_id.remaining_qty', string='Available',
                                 help='Quantity currently left in the sample.')
    date = fields.Date(required=True, default=fields.Date.context_today,
                       help='Date of the withdrawal.')
    purpose = fields.Selection([
        ('complaint', 'Complaint'),
        ('recall', 'Recall'),
        ('retest', 'Retest / Investigation'),
        ('periodic_exam', 'Periodic Examination'),
        ('other', 'Other'),
    ], required=True, help='Why the quantity was taken.')
    quantity = fields.Float(digits='Product Unit',
                            help='Quantity withdrawn. May be zero for a purely '
                                 'visual periodic examination.')
    reason = fields.Text(required=True,
                         help='Details of the withdrawal.')
    reference = fields.Char(help='Complaint, recall or investigation number.')
    owner_id = fields.Many2one('res.users', required=True,
                               default=lambda self: self.env.user,
                               help='Person responsible for the withdrawn material.')
    exam_result = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('unsatisfactory', 'Unsatisfactory'),
    ], string='Examination Result', help='Outcome of a periodic visual examination.')

    @api.constrains('quantity', 'purpose', 'exam_result')
    def _check_quantity(self):
        """Validate the withdrawn quantity and examination result."""
        for rec in self:
            if rec.quantity < 0:
                raise ValidationError(self.env._("A withdrawal quantity cannot be negative."))
            if rec.purpose != 'periodic_exam' and not rec.quantity:
                raise ValidationError(self.env._("Enter the quantity withdrawn."))
            if rec.purpose == 'periodic_exam' and not rec.exam_result:
                raise ValidationError(self.env._("Record the result of the periodic examination."))

    @api.model_create_multi
    def create(self, vals_list):
        """Check the sample can supply the quantity, then update it."""
        Sample = self.env['pharma.retention.sample']
        available = {}
        for vals in vals_list:
            sample = Sample.browse(vals.get('sample_id'))
            if sample.state != 'retained':
                raise UserError(self.env._("Nothing can be withdrawn from a disposed sample."))
            left = available.setdefault(sample.id, sample.remaining_qty)
            qty = vals.get('quantity') or 0.0
            rounding = sample.product_uom_id.rounding or 0.0001
            if float_compare(qty, left, precision_rounding=rounding) > 0:
                raise UserError(self.env._(
                    "Only %(avail)s %(uom)s is left in %(ref)s.",
                    avail=left, uom=sample.product_uom_id.name, ref=sample.name))
            available[sample.id] = left - qty
        records = super().create(vals_list)
        for rec in records:
            sample = rec.sample_id
            sample._pharma_after_withdrawal(rec)
            sample.message_post(body=self.env._(
                "Withdrawal (%(purpose)s): %(qty)s %(uom)s by %(owner)s. Remaining %(rem)s %(uom)s.",
                purpose=dict(self._fields['purpose'].selection)[rec.purpose],
                qty=rec.quantity, uom=sample.product_uom_id.name,
                owner=rec.owner_id.name, rem=sample.remaining_qty))
        return records

    def write(self, vals):
        """Withdrawal entries are part of the register and stay as recorded."""
        if vals:
            raise UserError(self.env._("A recorded withdrawal cannot be changed."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_never(self):
        """Withdrawal entries are part of the register and are never deleted."""
        raise UserError(self.env._("A recorded withdrawal cannot be deleted."))
