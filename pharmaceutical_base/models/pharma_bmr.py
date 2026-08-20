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
from odoo.exceptions import UserError
from odoo.tools.translate import _


YIELD_THRESHOLD = 95.0  # percent — BMR flags a QA review below this


class PharmaBMR(models.Model):
    """Batch Manufacturing Record (BMR)."""
    _name = 'pharma.bmr'
    _description = 'Batch Manufacturing Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='BMR Number',
        default='New',
        copy=False,
        readonly=True,
        tracking=True,
        help='Specifies the BMR Number for this record.',
    )
    production_id = fields.Many2one(
        comodel_name='mrp.production',
        string='Manufacturing Order',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
        help='Specifies the Manufacturing Order for this record.',
    )
    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Specifies the Product for this record.',
    )
    batch_no = fields.Char(
        string='Batch Number',
        required=True,
        copy=False,
        tracking=True,
        help='Unique batch number for this production run.',
    )
    enable_ipqc = fields.Boolean(
        string='IPQC Testing Required',
        default=False,
        tracking=True,
        help='Indicates whether In-Process Quality Control (IPQC) checks are required for this batch. '
             'If enabled, the IPQC Checks tab becomes visible so operators can log and sign off on '
             'quality parameters during execution. All required IPQC parameters must be completed '
             'and signed off before supervisor verification can be performed.',
    )
    any_step_operator_signed = fields.Boolean(
        compute='_compute_any_step_operator_signed',
        string='Any Step Signed by Operator',
    )
    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('on_hold', 'On Hold'),
            ('completed', 'Completed'),
        ],
        string='Status',
        default='draft',
        required=True,
        copy=False,
        tracking=True,
        help='Specifies the Status for this record.',
    )
    yield_expected = fields.Float(
        string='Expected Yield (unit)',
        digits=(16, 3),
        help='Theoretical yield based on BOM quantities.',
    )
    yield_actual = fields.Float(
        string='Actual Yield (unit)',
        digits=(16, 3),
        tracking=True,
        help='Actual output weight recorded at end of batch.',
    )
    yield_percentage = fields.Float(
        string='Yield %',
        compute='_compute_yield',
        store=True,
        digits=(5, 2),
        tracking=True,
        help='Specifies the Yield % for this record.',
    )
    yield_flag = fields.Boolean(
        string='Yield Flag',
        compute='_compute_yield',
        store=True,
        tracking=True,
        help='True when yield is below the configured threshold. '
             'QA sign-off is required before the BMR can be completed.',
    )
    qa_yield_signoff = fields.Boolean(
        string='QA Yield Sign-Off',
        copy=False,
        tracking=True,
        help='QA Director has reviewed and accepted a below-threshold yield.',
    )
    qa_yield_signed_by = fields.Many2one(
        comodel_name='res.users',
        string='Yield Sign-Off By',
        copy=False,
        readonly=True,
        tracking=True,
        help='Specifies the Yield Sign-Off By for this record.',
    )
    step_ids = fields.One2many(
        comodel_name='pharma.bmr.step',
        inverse_name='bmr_id',
        string='Steps',
        help='Specifies the Steps for this record.',
    )
    ipqc_ids = fields.One2many(
        comodel_name='pharma.ipqc.result',
        inverse_name='bmr_id',
        string='IPQC Results',
        help='Specifies the IPQC Results for this record.',
    )
    step_count = fields.Integer(
        compute='_compute_counts',
        help='Specifies the Step Count for this record.',
    )
    ipqc_count = fields.Integer(
        compute='_compute_counts',
        help='Specifies the Ipqc Count for this record.',
    )
    all_steps_done = fields.Boolean(help='Specifies the All Steps Done for this record.',
        string='All Steps Done',
        compute='_compute_all_steps_done',
    )

    _sql_constraints = [
        ('production_uniq', 'unique(production_id)', 'A Manufacturing Order can only have one BMR.')
    ]

    @api.depends('step_ids.operator_signed_on')
    def _compute_any_step_operator_signed(self):
        """Flag the BMR when at least one of its steps carries an operator signature."""
        for bmr in self:
            bmr.any_step_operator_signed = any(step.operator_signed_on for step in bmr.step_ids)

    @api.onchange('enable_ipqc')
    def _onchange_enable_ipqc(self):
        """Clear the IPQC checks when in-process quality control is switched off."""
        if not self.enable_ipqc:
            self.ipqc_ids = [(5, 0, 0)]

    @api.depends('step_ids.status')
    def _compute_all_steps_done(self):
        """Executes the _compute_all_steps_done operation."""
        for rec in self:
            if rec.step_ids:
                rec.all_steps_done = all(s.status == 'done' for s in rec.step_ids)
            else:
                rec.all_steps_done = False

    @api.depends('step_ids', 'ipqc_ids')
    def _compute_counts(self):
        """Count the execution steps and IPQC results linked to this BMR."""
        for rec in self:
            rec.step_count = len(rec.step_ids)
            rec.ipqc_count = len(rec.ipqc_ids)

    def action_view_steps(self):
        """Returns a window action to display all steps associated with this BMR."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("pharmaceutical_base.pharma_bmr_step_action")
        action['domain'] = [('bmr_id', '=', self.id)]
        action['context'] = {'default_bmr_id': self.id}
        return action

    def action_view_ipqc(self):
        """Open all IPQC results associated with this BMR."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("pharmaceutical_base.pharma_ipqc_result_action")
        action['domain'] = [('bmr_id', '=', self.id)]
        action['context'] = {'default_bmr_id': self.id}
        return action

    @api.depends('yield_expected', 'yield_actual')
    def _compute_yield(self):
        """Compute the actual yield percentage and flag low-yield batches."""
        for rec in self:
            if rec.yield_expected < rec.yield_actual:
                raise UserError(_('Actual Yield Must be greater than Expected Yield.'))
            if rec.yield_expected:
                pct = (rec.yield_actual / rec.yield_expected) * 100.0
            else:
                pct = 0.0
            rec.yield_percentage = pct
            rec.yield_flag = pct < YIELD_THRESHOLD and rec.yield_expected > 0

    @api.model_create_multi
    def create(self, vals_list):
        """Overrides creation to auto-assign a sequential BMR number."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('pharma.bmr') or 'New'
            if 'enable_ipqc' in vals and not vals['enable_ipqc']:
                vals['ipqc_ids'] = [(5, 0, 0)]
        return super().create(vals_list)

    def write(self, vals):
        """Drop the IPQC checks whenever in-process quality control is switched off."""
        if 'enable_ipqc' in vals and not vals['enable_ipqc']:
            vals['ipqc_ids'] = [(5, 0, 0)]
        return super().write(vals)

    def action_start(self):
        """Move BMR from Draft → In Progress."""
        for rec in self:
            if rec.status != 'draft':
                raise UserError(_('Only Draft BMRs can be started.'))
            if not rec.step_ids:
                raise UserError(_('Add at least one step before starting the BMR.'))
            rec.status = 'in_progress'
            rec.message_post(body=_('BMR started by %s.') % self.env.user.name)
        return True

    def action_hold(self):
        """Put the entire BMR On Hold."""
        for rec in self:
            if rec.status != 'in_progress':
                raise UserError(_('Only In Progress BMRs can be put on hold.'))
            rec.status = 'on_hold'
            rec.message_post(body=_('BMR placed on hold by %s.') % self.env.user.name)
        return True

    def action_resume(self):
        """Resume a BMR from On Hold → In Progress."""
        for rec in self:
            if rec.status != 'on_hold':
                raise UserError(_('Only On Hold BMRs can be resumed.'))
            # Check for open IPQCs on steps that are currently active or on hold
            active_step_ids = rec.step_ids.filtered(lambda s: s.status in ('in_progress', 'hold')).ids
            open_ipqcs = rec.ipqc_ids.filtered(lambda r: r.step_id.id in active_step_ids and not r.signed_on and r.result == 'fail')
            if open_ipqcs:
                raise UserError(_('Cannot resume — there are open IPQC failures that have not been signed/resolved.'))

            # Block resume while the batch has open Deviations / CAPAs. This
            # gate lives in the optional pharma_capa_deviation module (no-op
            # here when that module is not installed).
            rec._check_open_deviations_capas()

            # Ensure no step is still on hold
            held = rec.step_ids.filtered(lambda s: s.status == 'hold')
            if held:
                raise UserError(_(
                    'Cannot resume — the following step(s) are still on hold:\n%s'
                ) % '\n'.join(held.mapped('description')))
            rec.status = 'in_progress'
            rec.message_post(body=_('BMR resumed by %s.') % self.env.user.name)
        return True

    def _check_open_deviations_capas(self):
        """Hook to block resume on open deviations/CAPAs; no-op in core."""
        return

    def _check_ipqc_failure_deviations(self):
        """Hook: each failed IPQC check needs a closed deviation; no-op in core."""
        return

    def action_complete(self):
        """Move the BMR from In Progress to Completed once all gates pass."""
        self._check_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can mark a BMR as completed.'),
        )
        for rec in self:
            if rec.status != 'in_progress':
                raise UserError(_('Only In Progress BMRs can be completed.'))

            # Gate 1: all steps done
            non_done = rec.step_ids.filtered(lambda s: s.status != 'done')
            if non_done:
                raise UserError(_(
                    'Cannot complete — %d step(s) are not yet Done.'
                ) % len(non_done))

            # Gate 2: no unresolved IPQC failures. The deviation-based check
            # lives in the optional pharma_capa_deviation module (no-op here).
            rec._check_ipqc_failure_deviations()

            # Gate 3: yield flag requires QA sign-off
            if rec.yield_flag and not rec.qa_yield_signoff:
                raise UserError(_(
                    'Yield is below the %.1f%% threshold (actual: %.2f%%). '
                    'A QA Director must sign off on the yield before this BMR '
                    'can be completed.'
                ) % (YIELD_THRESHOLD, rec.yield_percentage))

            rec.status = 'completed'
            rec.message_post(body=_('BMR completed by %s.') % self.env.user.name)

            mo = rec.production_id
            if mo and mo.state not in ('done', 'cancel'):
                # Ensure the MO is fully produced and lands in the 'done' state.
                # Set the producing quantity if missing and skip the
                # consumption/backorder wizards so button_mark_done completes
                # instead of returning an interactive action.
                if not mo.qty_producing:
                    mo.qty_producing = mo.product_qty
                mo.with_context(
                    skip_consumption=True,
                    skip_backorder=True,
                    skip_sanity_check=True,
                ).button_mark_done()
                mo.message_post(body=_("BMR %s completed. Manufacturing Order closed automatically.") % rec.name)

            # Auto-create Finished Goods QC Test Order
            rec._create_fg_qc_test_order()

    def action_qa_yield_signoff(self):
        """QA Director accepts a below-threshold yield."""
        self._check_group(
            'pharmaceutical_base.group_pharma_qa_director',
            _('Only the Pharma QA Director can sign off on yield deviations.'),
        )
        for rec in self:
            # Actual yield must be recorded before QA can sign off on it.
            if not rec.yield_actual:
                raise UserError(_(
                    'Cannot sign off — the Actual Yield is zero. '
                    'Please record the actual yield before signing off on the yield.'
                ))
            if not rec.yield_flag:
                raise UserError(_('Yield sign-off is only required when the yield flag is set.'))
            rec.write({
                'qa_yield_signoff': True,
                'qa_yield_signed_by': self.env.user.id,
            })
            rec.message_post(
                body=_('Yield sign-off by QA Director %s. Yield: %.2f%%.') % (
                    self.env.user.name, rec.yield_percentage
                )
            )

    def _create_fg_qc_test_order(self):
        """Auto-create a Finished Goods QC Test Order when the BMR completes."""
        lot = None
        if self.production_id and self.production_id.lot_producing_ids:
            lot = self.production_id.lot_producing_ids[0]

        if not lot:
            self.message_post(body=_(
                'BMR completed but no finished lot found on the MO. '
                'Please create the Finished Goods QC Test Order manually.'
            ))
            return

        # BMR completion (a QA-manager action) auto-creates the finished-goods
        # QC test order. QA has no create right, so it is created elevated.
        self.env['pharma.qc.test.order'].sudo().create({
            'product_id': self.product_id.id,
            'lot_id': lot.id,
            'stage': 'finished',
        })
        self.message_post(body=_(
            'Finished Goods QC Test Order auto-created for lot %s.'
        ) % lot.name)

    def _check_group(self, group_xmlid, message):
        """Check whether the current user is in a given security group."""
        if not self.env.user.has_group(group_xmlid):
            raise UserError(message)
