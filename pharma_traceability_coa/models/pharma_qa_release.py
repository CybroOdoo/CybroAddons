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


class PharmaQaRelease(models.Model):
    """QA Release Queue — batch disposition, CoA generation, and lot release."""

    _name = 'pharma.qa.release'
    _description = 'QA Release Queue Record'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True,
        help='Unique QA release reference, generated from a sequence.',
    )
    production_id = fields.Many2one(
        'mrp.production',
        string='Manufacturing Order',
        required=True,
        readonly=True,
        tracking=True,
        help='Manufacturing order submitted for QA release.',
    )
    product_id = fields.Many2one(
        'product.template',
        related='production_id.product_id.product_tmpl_id',
        store=True,
        help='Product manufactured by the order.',
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Batch',
        readonly=True,
        tracking=True,
        help='Finished-goods lot to be released.',
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('released', 'Released'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        help='Draft records wait in the queue; released records have their CoA issued.',
    )
    coa_id = fields.Many2one(
        'pharma.coa',
        string='Certificate of Analysis',
        readonly=True,
        tracking=True,
        help='Certificate of Analysis issued when the batch was released.',
    )
    # Smart button counts
    bmr_count = fields.Integer(
        compute="_compute_counts", string="BMR", help='Number of batch manufacturing records of the order.'
    )
    qc_test_count = fields.Integer(
        compute="_compute_counts",
        string="QC Test Orders",
        help='Number of QC test orders of the batch and its raw-material lots.',
    )
    deviation_count = fields.Integer(
        compute="_compute_counts",
        string="Deviations",
        help='Number of deviations linked to the batch or its raw-material lots.',
    )
    capa_count = fields.Integer(
        compute="_compute_counts",
        string="CAPAs",
        help='Number of CAPAs linked to the batch or its raw-material lots.',
    )
    coa_count = fields.Integer(
        compute="_compute_counts", string="CoAs", help='Number of certificates issued for the lot.'
    )
    # Main details
    company_id = fields.Many2one(
        'res.company',
        related='production_id.company_id',
        string='Company',
        help='Company of the manufacturing order.',
    )
    manufacturing_date = fields.Date(
        related='lot_id.manufacture_date',
        string='Manufacturing Date',
        help='Manufacturing date of the lot.',
    )
    expiry_date = fields.Date(
        related='lot_id.expiry_date', string='Expiry Date', help='Expiry date of the lot.'
    )
    formula_version = fields.Char(
        related='production_id.bom_id.display_name',
        string='Formula Version',
        help='Approved formula (bill of materials) used for the batch.',
    )
    manufactured_by = fields.Many2one(
        'res.users',
        related='production_id.user_id',
        string='Manufactured By',
        help='User responsible for the manufacturing order.',
    )
    # Release Checklist
    bmr_completed = fields.Boolean(
        "BMR Completed",
        compute="_compute_checklist",
        help='Set when the batch manufacturing record is completed.',
    )
    fg_qc_passed = fields.Boolean(
        "Finished Goods QC Passed",
        compute="_compute_checklist",
        help='Set when every finished-goods QC test order of the lot has passed.',
    )
    no_open_deviations = fields.Boolean(
        compute="_compute_checklist",
        help='Set when no deviation on the batch or its raw-material lots is open or under investigation.',
    )
    no_open_capas = fields.Boolean(
        "No Open CAPAs",
        compute="_compute_checklist",
        help='Set when every CAPA of the batch deviations is closed.',
    )
    yield_within_threshold = fields.Boolean(
        compute="_compute_checklist",
        help='Set when the produced quantity is at least 90% of the planned quantity.',
    )
    all_bmr_steps_completed = fields.Boolean(
        "All Mandatory BMR Steps Completed",
        compute="_compute_checklist",
        help='Set when the batch manufacturing record, with all its mandatory steps, is completed.',
    )
    all_ipqc_passed = fields.Boolean(
        "All Required IPQC Checks Passed",
        compute="_compute_checklist",
        help='Set when every in-process QC test order of the lot has passed.',
    )
    stability_sampling_completed = fields.Boolean(
        "Stability Sampling Completed (if applicable)",
        help='Tick once stability samples have been taken, where the product requires them.',
    )
    regulatory_docs_verified = fields.Boolean(
        "Regulatory Documents Verified",
        help='Tick once QA has verified the regulatory documents of the batch.',
    )
    overall_status = fields.Selection(
        [('pending', 'Pending'), ('all_clear', 'All Clear')],
        compute="_compute_overall_status",
        help='All Clear when every automatic checklist item is met.',
    )
    # Finished Goods QC
    fg_qc_test_id = fields.Many2one(
        'pharma.qc.test.order',
        compute="_compute_fg_qc",
        string="QC Test Order",
        help='Latest finished-goods QC test order of the lot.',
    )
    fg_qc_status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('under_investigation', 'Under Investigation'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
        ],
        compute="_compute_fg_qc",
        string="QC Status",
        help='Status of the latest finished-goods QC test order.',
    )
    fg_qc_stage = fields.Selection(
        [('incoming', 'Incoming'), ('ipqc', 'In-Process'), ('finished', 'Finished Goods')],
        compute="_compute_fg_qc",
        string="Stage",
        help='Stage of the latest finished-goods QC test order.',
    )
    fg_qc_reviewed_by = fields.Many2one(
        'res.users',
        compute="_compute_fg_qc",
        string="Reviewed By",
        help='QA user who reviewed the latest finished-goods QC test order.',
    )
    # Yield Information
    expected_yield = fields.Float(
        compute="_compute_yield", help='Planned quantity of the manufacturing order.'
    )
    actual_yield = fields.Float(
        compute="_compute_yield", help='Produced quantity of the manufacturing order.'
    )
    yield_percentage = fields.Float(
        string="Yield %",
        compute="_compute_yield",
        help='Produced quantity as a share of the planned quantity.',
    )
    yield_flag = fields.Selection(
        [('within', 'Within Limit'), ('out', 'Out of Limit')],
        compute="_compute_yield",
        help='Within Limit when the yield is at least 90% of the planned quantity.',
    )
    # IPQC Information
    ipqc_ids = fields.One2many(
        comodel_name='pharma.ipqc.result',
        compute='_compute_ipqc_ids',
        string='IPQC Checks',
        help='In-process quality control check results for this batch.',
    )

    @api.depends('production_id')
    def _compute_ipqc_ids(self):
        """Collect the IPQC results recorded on the batch's BMR."""
        for rec in self:
            if rec.production_id:
                bmr = self.env['pharma.bmr'].search([('production_id', '=', rec.production_id.id)], limit=1)
                rec.ipqc_ids = bmr.ipqc_ids if bmr else self.env['pharma.ipqc.result']
            else:
                rec.ipqc_ids = self.env['pharma.ipqc.result']

    @api.depends('production_id', 'lot_id')
    def _compute_counts(self):
        """Count the BMRs, QC tests, deviations, CAPAs and CoAs of the batch."""
        for rec in self:
            # Counts span the finished lot and its raw-material lots.
            lot_ids = rec._batch_lot_ids()

            rec.bmr_count = (
                self.env['pharma.bmr'].search_count([('production_id', '=', rec.production_id.id)])
                if rec.production_id
                else 0
            )
            rec.qc_test_count = (
                self.env['pharma.qc.test.order'].search_count([('lot_id', 'in', lot_ids.ids)])
                if lot_ids
                else 0
            )
            if rec.production_id:
                devs = self.env['pharma.deviation'].search(
                    [
                        '|',
                        ('batch_id', '=', rec.production_id.id),
                        ('lot_id', 'in', lot_ids.ids),
                    ]
                )
                rec.deviation_count = len(devs)
                rec.capa_count = self.env['pharma.capa'].search_count([('deviation_id', 'in', devs.ids)])
            else:
                rec.deviation_count = 0
                rec.capa_count = 0
            rec.coa_count = (
                self.env['pharma.coa'].search_count([('lot_id', '=', rec.lot_id.id)]) if rec.lot_id else 0
            )

    @api.depends('production_id', 'lot_id')
    def _compute_checklist(self):
        """Evaluate the automatic items of the release checklist."""
        for rec in self:
            bmr = self.env['pharma.bmr'].search([('production_id', '=', rec.production_id.id)], limit=1)
            rec.bmr_completed = bool(bmr and bmr.status == 'completed')
            rec.all_bmr_steps_completed = bool(bmr and bmr.status == 'completed')

            fg_qc = self.env['pharma.qc.test.order'].search(
                [('lot_id', '=', rec.lot_id.id), ('stage', '=', 'finished')]
            )
            rec.fg_qc_passed = bool(fg_qc and all(q.status == 'passed' for q in fg_qc))

            ipqc = self.env['pharma.qc.test.order'].search(
                [('lot_id', '=', rec.lot_id.id), ('stage', '=', 'ipqc')]
            )
            rec.all_ipqc_passed = bool(not ipqc or all(q.status == 'passed' for q in ipqc))

            # Same scope as the counts: finished batch and its raw-material lots.
            devs = self.env['pharma.deviation'].search(
                [
                    '|',
                    ('batch_id', '=', rec.production_id.id),
                    ('lot_id', 'in', rec._batch_lot_ids().ids),
                ]
            )
            open_devs = len(devs.filtered(lambda d: d.status in ('open', 'under_investigation')))
            rec.no_open_deviations = open_devs == 0

            open_capas = self.env['pharma.capa'].search_count(
                [('deviation_id', 'in', devs.ids), ('status', '!=', 'closed')]
            )
            rec.no_open_capas = open_capas == 0

            expected = rec.production_id.product_qty or 1
            actual = rec.production_id.qty_producing or 0
            yield_pct = (actual / expected) * 100
            rec.yield_within_threshold = yield_pct >= 90.0

    @api.depends(
        'bmr_completed',
        'fg_qc_passed',
        'no_open_deviations',
        'no_open_capas',
        'yield_within_threshold',
        'all_bmr_steps_completed',
        'all_ipqc_passed',
    )
    def _compute_overall_status(self):
        """All Clear when every automatic checklist item is met."""
        for rec in self:
            if all(
                [
                    rec.bmr_completed,
                    rec.fg_qc_passed,
                    rec.no_open_deviations,
                    rec.no_open_capas,
                    rec.yield_within_threshold,
                    rec.all_bmr_steps_completed,
                    rec.all_ipqc_passed,
                ]
            ):
                rec.overall_status = 'all_clear'
            else:
                rec.overall_status = 'pending'

    @api.depends('lot_id')
    def _compute_fg_qc(self):
        """Show the latest finished-goods QC test order of the lot."""
        for rec in self:
            qc = self.env['pharma.qc.test.order'].search(
                [('lot_id', '=', rec.lot_id.id), ('stage', '=', 'finished')], limit=1, order="id desc"
            )
            rec.fg_qc_test_id = qc.id
            rec.fg_qc_status = qc.status if qc else False
            rec.fg_qc_stage = qc.stage if qc else False
            rec.fg_qc_reviewed_by = qc.reviewed_by.id if qc else False

    @api.depends('production_id')
    def _compute_yield(self):
        """Compare the produced quantity with the planned quantity."""
        for rec in self:
            expected = rec.production_id.product_qty or 0.0
            actual = rec.production_id.qty_producing or 0.0
            rec.expected_yield = expected
            rec.actual_yield = actual
            if expected > 0:
                pct = actual / expected
            else:
                pct = 0.0
            rec.yield_percentage = pct
            rec.yield_flag = 'within' if pct >= 0.90 else 'out'

    def action_view_bmr(self):
        """Open the batch manufacturing records of the order."""
        self.ensure_one()
        return {
            'name': self.env._('BMR'),
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.bmr',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.production_id.id)],
        }

    def action_view_qc_tests(self):
        """Open the QC test orders of the batch and its raw-material lots."""
        self.ensure_one()
        lot_ids = self._batch_lot_ids()
        return {
            'name': self.env._('QC Test Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.qc.test.order',
            'view_mode': 'list,form',
            'domain': [('lot_id', 'in', lot_ids.ids)],
        }

    def _batch_lot_ids(self):
        """Finished lot plus all consumed raw-material lots for this batch."""
        self.ensure_one()
        lot_ids = self.env['stock.lot']
        if self.lot_id:
            lot_ids |= self.lot_id
        if self.production_id:
            lot_ids |= self.production_id._pharma_raw_material_lots()
        return lot_ids

    def action_view_deviations(self):
        """Open the deviations of the batch and its raw-material lots."""
        self.ensure_one()
        lot_ids = self._batch_lot_ids()
        return {
            'name': self.env._('Deviations'),
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.deviation',
            'view_mode': 'list,form',
            # Finished-batch deviations (batch_id) OR raw-material lot deviations
            # (lot_id on any consumed lot).
            'domain': ['|', ('batch_id', '=', self.production_id.id), ('lot_id', 'in', lot_ids.ids)],
        }

    def action_view_capas(self):
        """Open the CAPAs of the batch and its raw-material lots."""
        self.ensure_one()
        lot_ids = self._batch_lot_ids()
        devs = self.env['pharma.deviation'].search(
            ['|', ('batch_id', '=', self.production_id.id), ('lot_id', 'in', lot_ids.ids)]
        )
        return {
            'name': self.env._('CAPAs'),
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.capa',
            'view_mode': 'list,form',
            'domain': [('deviation_id', 'in', devs.ids)],
        }

    def action_view_coa(self):
        """Open the certificates issued for the lot."""
        self.ensure_one()
        return {
            'name': self.env._('CoAs'),
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.coa',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.lot_id.id)],
        }

    def action_view_genealogy(self):
        """Open the batch genealogy of the lot."""
        self.ensure_one()
        if not self.lot_id:
            raise ValidationError(
                self.env._(
                    "No Lot/Batch is linked to this QA Release record yet, so batch genealogy cannot be shown."
                )
            )
        # The default stock.lot form does not show the genealogy notebook.
        return {
            'name': self.env._('Batch Genealogy'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'form',
            'views': [(self.env.ref('pharma_traceability_coa.stock_lot_genealogy_form').id, 'form')],
            'res_id': self.lot_id.id,
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Assign the next QA release reference."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('pharma.qa.release') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        """Release the batch after its QC, OOS and deviation checks, and issue a locked CoA."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            self.env._("Only QA can confirm and release a batch."),
        )
        # Releasing reads the order's moves, marks the lot Released and posts
        # on the order: Manufacturing / Inventory rights QA does not hold, so
        # the release runs elevated once the QA role check above has passed.
        for rec in self.sudo():
            if rec.state != 'draft':
                continue
            bmr = rec.production_id
            lot_ids = self.env['stock.lot']
            if rec.lot_id:
                lot_ids |= rec.lot_id
            if bmr:
                lot_ids |= bmr.move_raw_ids.mapped('move_line_ids.lot_id')

            qc_tests = self.env['pharma.qc.test.order'].search([('lot_id', 'in', lot_ids.ids)])
            if not qc_tests or not all(t.status == 'passed' for t in qc_tests):
                raise ValidationError(
                    self.env._("All QC Test Orders for the produced lots must be passed before QA Release.")
                )

            open_oos = self.env['pharma.oos.investigation'].search_count(
                [('result_line_id.test_order_id', 'in', qc_tests.ids), ('closed_on', '=', False)]
            )
            if open_oos > 0:
                raise ValidationError(
                    self.env._(
                        "There are open OOS investigations for this batch. They must be closed before QA Release."
                    )
                )

            open_deviations = self.env['pharma.deviation'].search_count(
                [('batch_id', '=', bmr.id), ('status', 'in', ('open', 'under_investigation'))]
            )
            if open_deviations > 0:
                raise ValidationError(
                    self.env._(
                        "There are open or under investigation deviations for this batch. "
                        "They must be resolved before QA Release."
                    )
                )

            passed_tests = qc_tests.filtered(lambda t: t.status == 'passed')
            primary_test_order = passed_tests[0] if passed_tests else False

            coa_vals = {
                'batch_id': bmr.id,
                'product_id': rec.product_id.id,
                'lot_id': rec.lot_id.id,
                'released_by': self.env.user.id,
                'release_date': fields.Datetime.now(),
                'qc_test_order_id': primary_test_order.id if primary_test_order else False,
                'is_locked': True,
            }

            lines = []
            for order in passed_tests:
                for res_line in order.result_line_ids:
                    mapped_status = 'pass' if res_line.status == 'pass' else 'oos'
                    lines.append(
                        (
                            0,
                            0,
                            {
                                'parameter': res_line.parameter,
                                'expected_min': res_line.expected_min,
                                'expected_max': res_line.expected_max,
                                'actual_value': res_line.actual_value,
                                'uom': res_line.uom,
                                'status': mapped_status,
                            },
                        )
                    )
            for ipqc in rec.ipqc_ids:
                if ipqc.parameter_id:
                    mapped_status = (
                        'pass' if ipqc.result == 'pass' else ('oos' if ipqc.result == 'fail' else 'pending')
                    )
                    lines.append(
                        (
                            0,
                            0,
                            {
                                'parameter': ipqc.parameter or ipqc.parameter_id.parameter_name,
                                'expected_min': ipqc.expected_min,
                                'expected_max': ipqc.expected_max,
                                'actual_value': ipqc.actual_value,
                                'uom': ipqc.parameter_id.uom_id.name if ipqc.parameter_id.uom_id else '',
                                'status': mapped_status,
                            },
                        )
                    )
            coa_vals['coa_line_ids'] = lines

            # QA has no create right, so the CoA is created elevated.
            coa = self.env['pharma.coa'].sudo().create(coa_vals)
            rec.coa_id = coa.id
            rec.state = 'released'

            if rec.lot_id:
                rec.lot_id.write({'lot_status': 'released'})

            bmr.message_post(
                body=self.env._(
                    "Batch released by QA. Certificate of Analysis %s has been generated.", coa.name
                )
            )
