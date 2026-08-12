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

from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

# Days added to raised_on to compute deadline per classification
_DEADLINE_DAYS = {
    'critical': 3,
    'major': 7,
    'minor': 14,
}


class PharmaDeviation(models.Model):
    """Deviation — a record of something that went wrong during manufacturing."""
    _name = 'pharma.deviation'
    _description = 'Pharma Deviation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']
    _order = 'name desc'
    name = fields.Char(
        string='Deviation Number',
        default='New',
        copy=False,
        readonly=True,
        tracking=True,
        help='Auto-generated, permanent — cannot be edited after creation.',
    )

    batch_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Manufacturing Order / Batch',
        ondelete='restrict',
        index=True,
        tracking=True,
            help='Specifies the Manufacturing Order / Batch for this record.',
    )

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot / Batch',
        ondelete='restrict',
        tracking=True,
            help='Specifies the Lot / Batch for this record.',
    )

    qc_result_id = fields.Many2one(
        comodel_name='pharma.qc.result.line',
        string='OOS QC Result (if applicable)',
        ondelete='set null',
        help='QC result that auto-triggered this deviation, if applicable.',
    )

    oos_investigation_id = fields.Many2one(
        comodel_name='pharma.oos.investigation',
        string='OOS Investigation',
        ondelete='set null',
        help='OOS investigation that triggered this deviation.',
    )
    stage = fields.Selection(
        selection=[
            ('manufacturing', 'Manufacturing'),
            ('qc', 'QC'),
            ('packaging', 'Packaging'),
        ],
        string='Stage',
        required=True,
        tracking=True,
            help='Specifies the Stage for this record.',
    )

    classification = fields.Selection(
        selection=[
            ('critical', 'Critical'),
            ('major', 'Major'),
            ('minor', 'Minor'),
        ],
        string='Classification',
        required=True,
        default='major',
        tracking=True,
            help='Specifies the Classification for this record.',
    )

    root_cause_category = fields.Selection(
        selection=[
            ('human', 'Human'),
            ('equipment', 'Equipment'),
            ('material', 'Material'),
            ('method', 'Method'),
            ('environment', 'Environment'),
        ],
        string='Root Cause Category',
        tracking=True,
        help='Structured category for trend analysis across batches.',
    )
    description = fields.Text(
        string='Description',
        required=True,
        help='Full description of what went wrong.',
    )

    immediate_action = fields.Text(
        string='Immediate Action',
        help='Action taken immediately when the deviation was discovered.',
    )
    status = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('under_investigation', 'Under Investigation'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='open',
        required=True,
        copy=False,
        tracking=True,
            help='Specifies the Status for this record.',
    )
    raised_by = fields.Many2one(
        comodel_name='res.users',
        string='Raised By',
        default=lambda self: self.env.user,
        readonly=True,
        tracking=True,
            help='Specifies the Raised By for this record.',
    )

    raised_on = fields.Datetime(
        string='Raised On',
        default=fields.Datetime.now,
        readonly=True,
        tracking=True,
            help='Specifies the Raised On for this record.',
    )

    deadline_date = fields.Date(
        string='Investigation Deadline',
        compute='_compute_deadline',
        store=True,
        tracking=True,
        help='Raised On + 3/7/14 days for Critical/Major/Minor.',
    )
    disposition = fields.Selection(
        selection=[
            ('release', 'Release'),
            ('reject', 'Reject'),
        ],
        string='Disposition',
        copy=False,
        tracking=True,
        help='Final decision on the batch — must be set before closing.',
    )
    capa_ids = fields.One2many(
        comodel_name='pharma.capa',
        inverse_name='deviation_id',
        string='CAPAs',
            help='Specifies the CAPAs for this record.',
    )

    capa_count = fields.Integer(
        compute='_compute_capa_count',
            help='Specifies the Capa Count for this record.',
    )

    @api.depends('capa_ids')
    def _compute_capa_count(self):
        """Calculates the total number of CAPAs linked to this deviation."""
        for rec in self:
            rec.capa_count = len(rec.capa_ids)

    all_capas_closed = fields.Boolean(
        string='All CAPAs Closed',
        compute='_compute_all_capas_closed',
        help='True when there are no open CAPAs linked to this deviation.',
    )

    @api.depends('capa_ids', 'capa_ids.status')
    def _compute_all_capas_closed(self):
        """Determines if all CAPAs linked to this deviation have been successfully closed."""
        for rec in self:
            if not rec.capa_ids:
                rec.all_capas_closed = False
            else:
                rec.all_capas_closed = all(c.status == 'closed' for c in rec.capa_ids)

    @api.depends('raised_on', 'classification')
    def _compute_deadline(self):
        """Compute the investigation deadline from severity and creation date."""
        for rec in self:
            if rec.raised_on and rec.classification:
                days = _DEADLINE_DAYS.get(rec.classification, 7)
                rec.deadline_date = (rec.raised_on + timedelta(days=days)).date()
            else:
                rec.deadline_date = False

    @api.model_create_multi
    def create(self, vals_list):
        """Overrides creation to auto-assign a sequential deviation number."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('pharma.deviation') or 'New'
                )
        return super().create(vals_list)

    def write(self, vals):
        # Protect the permanent deviation number
        """Overrides write to protect the permanent deviation number from manual edits."""
        if 'name' in vals:
            for rec in self:
                if rec.name and rec.name != 'New':
                    raise UserError(_(
                        'The deviation number "%s" is permanent and cannot be edited.'
                    ) % rec.name)
        return super().write(vals)

    def action_investigate(self):
        """Move the deviation to Under Investigation and raise a CAPA."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can start a deviation investigation.'),
        )
        for rec in self:
            if rec.status not in ('open',):
                raise UserError(_('Only Open deviations can be moved to Under Investigation.'))
            rec.status = 'under_investigation'
            rec.message_post(
                body=_('Deviation moved to Under Investigation by %s.') % self.env.user.name
            )
            if not rec.capa_ids:
                # CAPA is auto-raised by the (QA) investigation; QA has no
                # create right, so the downstream CAPA is created elevated.
                self.env['pharma.capa'].sudo().create({
                    'deviation_id': rec.id,
                    'capa_type': 'corrective',
                    'assigned_to': self.env.user.id,
                    'due_date': rec.deadline_date,
                })
                rec.message_post(
                    body=_('CAPA auto-raised from deviation %s.') % rec.name
                )

    def action_close(self):
        """Close the deviation once disposition is set and all CAPAs are closed."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can close a deviation.'),
        )
        for rec in self:
            if rec.status != 'under_investigation':
                raise UserError(_('Only deviations Under Investigation can be closed.'))
            if not rec.disposition:
                raise UserError(_(
                    'Set a Disposition (Release / Reject) before closing deviation %s.'
                ) % rec.name)
            if not rec.capa_ids:
                raise UserError(_(
                    'At least one CAPA must be raised before closing deviation %s.'
                ) % rec.name)
            open_capas = rec.capa_ids.filtered(lambda c: c.status != 'closed')
            if open_capas:
                raise UserError(_(
                    'All CAPAs must be closed before closing deviation %s. '
                    'Open CAPAs: %s'
                ) % (rec.name, ', '.join(open_capas.mapped('name'))))
            rec.status = 'closed'
            if rec.oos_investigation_id and rec.disposition == 'release':
                qc_test = rec.oos_investigation_id.result_line_id.test_order_id
                if qc_test:
                    qc_test.write({'status': 'passed'})
            elif rec.disposition == 'reject':
                rec._pharma_dispose_rejected_lot()

            rec.message_post(
                body=_(
                    'Deviation closed by %s. Disposition: %s.'
                ) % (self.env.user.name, dict(rec._fields['disposition'].selection).get(
                    rec.disposition, rec.disposition
                ))
            )

    def _pharma_dispose_rejected_lot(self):
        """Segregate the deviation's batch into the company's Rejected location."""
        # Physical counterpart of a 'Reject' disposition: the move
        # pharmaceutical_base would make at QC-fail time happens here instead,
        # once every CAPA is closed and QA has closed the deviation on a reject.
        # Not limited to incoming material — a rejected finished or in-process
        # batch must be segregated too. No on-hand stock is a no-op downstream.
        self.ensure_one()
        lot = self.lot_id or self.oos_investigation_id.lot_id
        if not lot:
            return
        lot.action_reject_lot()
        company = lot.company_id or self.env.company
        dest = company.pharma_rejected_location_id
        if not dest:
            self.message_post(body=_(
                'Deviation closed as Rejected, but no Rejected Location is '
                'configured, so lot %s was not segregated. Set one under '
                'Settings > Pharmaceutical ERP > Inventory & Quality Locations.'
            ) % lot.name)
            return
        # QA can approve/reject but has no create right on stock.picking, so
        # the disposition transfer is built elevated (same as the CAPA above).
        if lot.sudo()._pharma_create_disposition_transfer(dest):
            self.message_post(body=_(
                'Lot %s moved to the Rejected location %s.'
            ) % (lot.name, dest.complete_name))
