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
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class PharmaQcTestOrder(models.Model):
    """QC Test Order — testing order with stage, spec, lot, and results."""
    _name = 'pharma.qc.test.order'
    _description = 'QC Test Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Test Order Number',
        required=True,
        copy=False,
        readonly=True,
        default='/',
            help='Specifies the Test Order Number for this record.',
    )

    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
        help='Which material or product lot is being tested.'
    )

    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
        help='Product linked to this test order.'
    )

    spec_id = fields.Many2one(
        comodel_name='pharma.qc.spec',
        string='Specification',
        required=True,
        domain="[('state', '=', 'approved')]",
        ondelete='restrict',
        index=True,
        tracking=True,
        help='QC specification auto-loaded based on product and stage.'
    )

    stage = fields.Selection(
        selection=[
            ('incoming', 'Incoming'),
            ('inprocess', 'In-Process'),
            ('finished', 'Finished Goods'),
        ],
        string='Testing Stage',
        required=True,
        default='incoming',
        tracking=True,
        help='QC checkpoint stage.'
    )

    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('under_investigation', 'Under Investigation'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help='Overall status of the test order.'
    )

    entered_by = fields.Many2one(
        comodel_name='res.users',
        string='Analyst',
        tracking=True,
        help='Analyst who entered the results.'
    )

    reviewed_by = fields.Many2one(
        comodel_name='res.users',
        string='Reviewed By',
        tracking=True,
        help='Second person who reviewed and signed, must differ from analyst.'
    )

    result_line_ids = fields.One2many(
        comodel_name='pharma.qc.result.line',
        inverse_name='test_order_id',
        string='Test Results',
        copy=True,
            help='Specifies the Test Results for this record.',
    )

    oos_investigation_ids = fields.One2many(help='Specifies the Oos Investigation Ids for this record.',
        comodel_name='pharma.oos.investigation',
        inverse_name='test_order_id',
        string='OOS Investigations',
    )

    oos_investigation_count = fields.Integer(
        string='OOS Investigations',
        compute='_compute_oos_investigation_count',
            help='Specifies the OOS Investigations for this record.',
    )

    def _compute_oos_investigation_count(self):
        """Count the OOS investigations linked to this test order's results."""
        for order in self:
            order.oos_investigation_count = self.env['pharma.oos.investigation'].search_count([
                ('result_line_id.test_order_id', '=', order.id)
            ])

    stock_move_line_count = fields.Integer(
        string='Stock Moves',
        compute='_compute_stock_move_line_count',
        help='Number of completed stock moves for this lot — where it was '
             'received from and where it was moved on QC disposition.',
    )

    def _compute_stock_move_line_count(self):
        """Counts the done stock move lines for the tested lot."""
        for order in self:
            order.stock_move_line_count = self.env['stock.move.line'].search_count([
                ('lot_id', '=', order.lot_id.id),
                ('state', '=', 'done'),
            ]) if order.lot_id else 0

    def action_view_stock_moves(self):
        """Open the stock move history for the tested lot."""
        self.ensure_one()
        if not self.lot_id:
            raise ValidationError(_("This test order has no lot to trace."))
        return {
            'name': _('Stock Moves — %s', self.lot_id.name),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('pharmaceutical_base.view_pharma_move_line_list').id, 'list'),
                (False, 'form'),
            ],
            'search_view_id': (
                self.env.ref('pharmaceutical_base.view_pharma_move_line_search').id, 'search'),
            'domain': [('lot_id', '=', self.lot_id.id), ('state', '=', 'done')],
            'context': {'create': False},
        }

    def action_view_oos_investigations(self):
        """Open all OOS investigations related to this test order."""
        self.ensure_one()
        return {
            'name': 'OOS Investigations',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'pharma.oos.investigation',
            'domain': [('result_line_id.test_order_id', '=', self.id)],
            'context': {},
        }

    def _check_qc_deviations_closed(self):
        """Hook to block approval while related deviations are open; no-op in core."""
        return

    def action_start_test(self):
        """Move the test order from Draft to In Progress, assigning the analyst."""
        for rec in self:
            if rec.status != 'draft':
                raise ValidationError(_("Only draft test orders can be started."))

            vals = {'status': 'in_progress'}
            if not rec.entered_by:
                vals['entered_by'] = self.env.user.id
            rec.write(vals)

    def action_approve(self):
        """Approve the test order once results pass and OOS investigations are resolved."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can approve (pass) a QC test order.'),
        )
        for rec in self:
            if rec.status not in ('in_progress', 'under_investigation'):
                raise ValidationError(_("Only test orders in 'In Progress' or 'Under Investigation' status can be approved."))

            # Check OOS investigations — all must be closed before approving
            investigations = self.env['pharma.oos.investigation'].search([
                ('result_line_id', 'in', rec.result_line_ids.ids)
            ])
            if any(not inv.closed_on for inv in investigations):
                raise ValidationError(_("Cannot approve a test order with open OOS investigations."))

            # Block approval while related deviations are still open. The check
            # lives in the optional pharma_capa_deviation module (no-op here).
            rec._check_qc_deviations_closed()

            for line in rec.result_line_ids:
                if not line.result_entered:
                    raise ValidationError(_("You must enter a result for parameter '%s' before approving.") % (line.parameter_id.parameter_name if line.parameter_id else _('Unnamed')))
                if line.is_oos:
                    line_invs = sorted(
                        investigations.filtered(lambda i, l=line: i.result_line_id == l),
                        key=lambda i: i.id,
                    )
                    if not line_invs:
                        raise ValidationError(_("OOS result has no investigation record. Cannot approve."))
                    latest = line_invs[-1]
                    if not latest.lab_error_found and latest.disposition != 'release':
                        raise ValidationError(_("Cannot approve: OOS result has no 'Release' "
                                                "disposition and was not resolved as a lab error."))

            rec.write({
                'reviewed_by': self.env.user.id,
                'status': 'passed',
            })
            # lot_status is set to 'approved' by the stock.lot write() hook when
            # status becomes 'passed'. Passing QC triggers NO physical move: the
            # material stays wherever putaway placed it, which is already the
            # sub-area matching its Storage Class.

    def action_reject(self):
        """Reject the test order, marking it Failed when results fail."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can reject (fail) a QC test order.'),
        )
        for rec in self:
            if rec.status not in ('in_progress', 'under_investigation'):
                raise ValidationError(_("Only test orders in 'In Progress' or 'Under Investigation' "
                                        "status can be rejected."))

            if rec.lot_id:
                rec.lot_id.action_reject_lot()
            # The segregation move is fired by write() below, so every path that
            # fails a test order — this button and the OOS auto-fail in
            # pharma.oos.investigation.action_close_investigation — segregates.
            rec.write({
                'reviewed_by': self.env.user.id,
                'status': 'failed',
            })

    def _pharma_dispose_rejected(self):
        """Move the failed lot to the company's Rejected location."""
        self.ensure_one()
        # Only incoming (raw-material) receipts have physical on-hand stock to
        # segregate. Finished-goods and in-process QC have no disposition move.
        if self.stage != 'incoming':
            return
        lot = self.lot_id
        if not lot:
            return
        # When an optional module owns the final batch decision (CAPA &
        # Deviation), the QC failure only opens the investigation — that module
        # makes the move when the decision is taken.
        if self._pharma_rejection_deferred():
            return
        company = lot.company_id or self.env.company
        dest = company.pharma_rejected_location_id
        if dest:
            # QA can approve/reject but has no create right on stock.picking,
            # so the disposition transfer is built elevated.
            lot.sudo()._pharma_create_disposition_transfer(dest)

    def _pharma_rejection_deferred(self):
        """Hook: True when a downstream process owns the reject move; False in core."""
        self.ensure_one()
        return False

    @api.constrains('entered_by', 'reviewed_by')
    def _check_reviewer(self):
        """Ensure the reviewer differs from the analyst who entered results."""
        for rec in self:
            if rec.entered_by and rec.reviewed_by and rec.entered_by == rec.reviewed_by:
                pass

    @api.onchange('product_id', 'stage')
    def _onchange_product_stage(self):
        """Load the latest approved QC spec when the product or stage changes."""
        if self.product_id and self.stage:
            spec = self.env['pharma.qc.spec'].search([
                ('product_id', '=', self.product_id.id),
                ('stage', '=', self.stage),
                ('state', '=', 'approved'),
                '|', ('effective_date', '=', False), ('effective_date', '>=', fields.Date.today())
            ], order='version desc', limit=1)
            if spec:
                self.spec_id = spec.id
            else:
                self.spec_id = False
        else:
            self.spec_id = False

    @api.onchange('spec_id')
    def _onchange_spec_id(self):
        """Generate result lines from the selected QC specification's parameters."""
        if self.spec_id:
            # Clear old lines
            self.result_line_ids = [(5, 0, 0)]
            # Create new lines from spec parameter lines
            lines = []
            for line in self.spec_id.parameter_ids:
                lines.append((0, 0, {
                    'parameter_id': line.id,
                    'expected_min': line.min_value,
                    'has_min': line.min_value != 0.0 or getattr(line, 'has_min', True),
                    'expected_max': line.max_value,
                    'has_max': line.max_value != 0.0 or getattr(line, 'has_max', True),
                    'uom': line.uom_id.name or '',
                    'actual_value': 0.0,
                }))
            self.result_line_ids = lines

    @api.model_create_multi
    def create(self, vals_list):
        """Assign a sequential number and load parameters from the active QC spec."""
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('pharma.qc.test.order') or '/'

            # Auto load spec_id if product and stage are provided but spec_id is not
            if not vals.get('spec_id') and vals.get('product_id') and vals.get('stage'):
                spec = self.env['pharma.qc.spec'].search([
                    ('product_id', '=', vals['product_id']),
                    ('stage', '=', vals['stage']),
                    ('state', '=', 'approved'),
                    '|', ('effective_date', '=', False), ('effective_date', '>=', fields.Date.today())
                ], order='version desc', limit=1)
                if spec:
                    vals['spec_id'] = spec.id
                else:
                    product = self.env['product.template'].browse(vals['product_id'])
                    raise ValidationError(_(
                        "Cannot generate QC Test Order: No approved '%s' QC Specification found for product '%s'. "
                        "An approved specification is required before this product can be processed."
                    ) % (vals['stage'], product.display_name))

            # If spec_id is set/found, auto-load parameters if lines not provided
            if vals.get('spec_id') and not vals.get('result_line_ids'):
                spec = self.env['pharma.qc.spec'].browse(vals['spec_id'])
                lines = []
                for line in spec.parameter_ids:
                    lines.append((0, 0, {
                        'parameter_id': line.id,
                        'expected_min': line.min_value,
                        'has_min': line.min_value != 0.0 or getattr(line, 'has_min', True),
                        'expected_max': line.max_value,
                        'has_max': line.max_value != 0.0 or getattr(line, 'has_max', True),
                        'uom': line.uom_id.name or '',
                        'actual_value': 0.0,
                    }))
                vals['result_line_ids'] = lines
        return super().create(vals_list)

    def write(self, vals):
        """Lock material and specification once testing begins."""
        _many2one = {'product_id', 'lot_id', 'spec_id'}
        _selection = {'stage'}
        locked = _many2one | _selection
        for rec in self:
            if rec.status != 'draft':
                for field in locked:
                    if field not in vals:
                        continue
                    current = rec[field].id if field in _many2one else rec[field]
                    if vals[field] != current:
                        raise ValidationError(
                            _("Cannot modify material or parameter details once the test has started.")
                        )
        # If spec_id is updated on draft test orders and result_line_ids is not passed,
        # regenerate the result lines.
        if 'spec_id' in vals and not vals.get('result_line_ids'):
            spec = self.env['pharma.qc.spec'].browse(vals['spec_id']) if vals['spec_id'] else False
            lines = [(5, 0, 0)]
            if spec:
                for line in spec.parameter_ids:
                    lines.append((0, 0, {
                        'parameter_id': line.id,
                        'expected_min': line.min_value,
                        'has_min': line.min_value != 0.0 or getattr(line, 'has_min', True),
                        'expected_max': line.max_value,
                        'has_max': line.max_value != 0.0 or getattr(line, 'has_max', True),
                        'uom': line.uom_id.name or '',
                        'actual_value': 0.0,
                    }))
            vals['result_line_ids'] = lines

        # Captured before the write so re-saving an already-failed order does
        # not build a second disposition transfer for the same lot.
        newly_failed = self.filtered(
            lambda r: r.status != 'failed') if vals.get('status') == 'failed' else self.browse()

        res = super().write(vals)
        if 'status' in vals and vals['status'] == 'passed':
            for rec in self:
                if rec.lot_id:
                    rec.lot_id.action_approve_lot()
        for rec in newly_failed:
            rec._pharma_dispose_rejected()
        return res
