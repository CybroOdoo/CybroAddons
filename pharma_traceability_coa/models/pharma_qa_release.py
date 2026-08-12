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

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New', tracking=True, help='Specifies the Name for this record.')
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order', required=True, readonly=True, tracking=True, help='Specifies the Production Id for this record.')
    product_id = fields.Many2one('product.template', related='production_id.product_id.product_tmpl_id', store=True, help='Specifies the Product Id for this record.')
    lot_id = fields.Many2one('stock.lot', string='Lot/Batch', readonly=True, tracking=True, help='Specifies the Lot Id for this record.')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('released', 'Released'),
    ], string='Status', default='draft', tracking=True, help='Specifies the State for this record.')
    coa_id = fields.Many2one('pharma.coa', string='Certificate of Analysis', readonly=True, tracking=True, help='Specifies the Coa Id for this record.')

    # Smart button counts
    bmr_count = fields.Integer(compute="_compute_counts", string="BMR", help='Specifies the Bmr Count for this record.')
    qc_test_count = fields.Integer(compute="_compute_counts", string="QC Test Orders", help='Specifies the Qc Test Count for this record.')
    deviation_count = fields.Integer(compute="_compute_counts", string="Deviations", help='Specifies the Deviation Count for this record.')
    capa_count = fields.Integer(compute="_compute_counts", string="CAPAs", help='Specifies the Capa Count for this record.')
    coa_count = fields.Integer(compute="_compute_counts", string="CoAs", help='Specifies the Coa Count for this record.')

    # Main details
    company_id = fields.Many2one('res.company', related='production_id.company_id', string='Company', help='Specifies the Company Id for this record.')
    manufacturing_date = fields.Date(related='lot_id.manufacture_date', string='Manufacturing Date', help='Specifies the Manufacturing Date for this record.')
    expiry_date = fields.Date(related='lot_id.expiry_date', string='Expiry Date', help='Specifies the Expiry Date for this record.')
    formula_version = fields.Char(related='production_id.bom_id.display_name', string='Formula Version', help='Specifies the Formula Version for this record.')
    manufactured_by = fields.Many2one('res.users', related='production_id.user_id', string='Manufactured By', help='Specifies the Manufactured By for this record.')

    # Release Checklist
    bmr_completed = fields.Boolean("BMR Completed", compute="_compute_checklist", help='Specifies the Bmr Completed for this record.')
    fg_qc_passed = fields.Boolean("Finished Goods QC Passed", compute="_compute_checklist", help='Specifies the Fg Qc Passed for this record.')
    no_open_deviations = fields.Boolean("No Open Deviations", compute="_compute_checklist", help='Specifies the No Open Deviations for this record.')
    no_open_capas = fields.Boolean("No Open CAPAs", compute="_compute_checklist", help='Specifies the No Open Capas for this record.')
    yield_within_threshold = fields.Boolean("Yield Within Threshold", compute="_compute_checklist", help='Specifies the Yield Within Threshold for this record.')
    all_bmr_steps_completed = fields.Boolean("All Mandatory BMR Steps Completed", compute="_compute_checklist", help='Specifies the All Bmr Steps Completed for this record.')
    all_ipqc_passed = fields.Boolean("All Required IPQC Checks Passed", compute="_compute_checklist", help='Specifies the All Ipqc Passed for this record.')
    stability_sampling_completed = fields.Boolean("Stability Sampling Completed (if applicable)", help='Specifies the Stability Sampling Completed for this record.')
    regulatory_docs_verified = fields.Boolean("Regulatory Documents Verified", help='Specifies the Regulatory Docs Verified for this record.')
    overall_status = fields.Selection([('pending', 'Pending'), ('all_clear', 'All Clear')], compute="_compute_overall_status", help='Specifies the Overall Status for this record.')

    # Finished Goods QC
    fg_qc_test_id = fields.Many2one('pharma.qc.test.order', compute="_compute_fg_qc", string="QC Test Order", help='Specifies the Fg Qc Test Id for this record.')
    fg_qc_status = fields.Selection([
        ('draft', 'Draft'), ('in_progress', 'In Progress'), ('under_investigation', 'Under Investigation'),
        ('passed', 'Passed'), ('failed', 'Failed')
    ], compute="_compute_fg_qc", string="QC Status", help='Specifies the Fg Qc Status for this record.')
    fg_qc_stage = fields.Selection([
        ('incoming', 'Incoming'), ('inprocess', 'In-Process'), ('finished', 'Finished Goods')
    ], compute="_compute_fg_qc", string="Stage", help='Specifies the Fg Qc Stage for this record.')
    fg_qc_reviewed_by = fields.Many2one('res.users', compute="_compute_fg_qc", string="Reviewed By", help='Specifies the Fg Qc Reviewed By for this record.')

    # Yield Information
    expected_yield = fields.Float(string="Expected Yield", compute="_compute_yield", help='Specifies the Expected Yield for this record.')
    actual_yield = fields.Float(string="Actual Yield", compute="_compute_yield", help='Specifies the Actual Yield for this record.')
    yield_percentage = fields.Float(string="Yield %", compute="_compute_yield", help='Specifies the Yield Percentage for this record.')
    yield_flag = fields.Char(string="Yield Flag", compute="_compute_yield", help='Specifies the Yield Flag for this record.')

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
        """Executes the _compute_counts operation."""
        for rec in self:
            # Finished lot + inferred raw-material lots (see _batch_lot_ids) so
            # the QC / Deviation / CAPA counts span raw materials too.
            lot_ids = rec._batch_lot_ids()

            rec.bmr_count = self.env['pharma.bmr'].search_count([('production_id', '=', rec.production_id.id)]) if rec.production_id else 0
            rec.qc_test_count = self.env['pharma.qc.test.order'].search_count([('lot_id', 'in', lot_ids.ids)]) if lot_ids else 0
            # Deviation / CAPA counts — guarded soft-reference: 0 when the optional
            # pharma_capa_deviation module is not installed. Span the finished
            # batch AND its consumed raw-material lots (lot_ids), so deviations
            # counted alongside the finished-batch deviations.
            if rec.production_id and 'pharma.deviation' in self.env:
                devs = self.env['pharma.deviation'].search([
                    '|',
                    ('batch_id', '=', rec.production_id.id),
                    ('lot_id', 'in', lot_ids.ids),
                ])
                rec.deviation_count = len(devs)
                rec.capa_count = self.env['pharma.capa'].search_count([('deviation_id', 'in', devs.ids)])
            else:
                rec.deviation_count = 0
                rec.capa_count = 0
            rec.coa_count = self.env['pharma.coa'].search_count([('lot_id', '=', rec.lot_id.id)]) if rec.lot_id else 0

    @api.depends('production_id', 'lot_id')
    def _compute_checklist(self):
        """Executes the _compute_checklist operation."""
        for rec in self:
            bmr = self.env['pharma.bmr'].search([('production_id', '=', rec.production_id.id)], limit=1)
            rec.bmr_completed = bool(bmr and bmr.status == 'completed')
            rec.all_bmr_steps_completed = bool(bmr and bmr.status == 'completed') # simplified

            fg_qc = self.env['pharma.qc.test.order'].search([
                ('lot_id', '=', rec.lot_id.id),
                ('stage', 'in', ('finished', 'finished_product'))
            ])
            rec.fg_qc_passed = bool(fg_qc and all(q.status == 'passed' for q in fg_qc))

            ipqc = self.env['pharma.qc.test.order'].search([
                ('lot_id', '=', rec.lot_id.id),
                ('stage', '=', 'in_process')
            ])
            rec.all_ipqc_passed = bool(not ipqc or all(q.status == 'passed' for q in ipqc))

            # Deviation / CAPA checklist — guarded soft-reference. With the CAPA
            # module absent there are no deviations/CAPAs, so both checks pass.
            if 'pharma.deviation' in self.env:
                open_devs = self.env['pharma.deviation'].search_count([
                    ('batch_id', '=', rec.production_id.id),
                    ('status', 'in', ('open', 'under_investigation'))
                ])
                rec.no_open_deviations = (open_devs == 0)

                open_capas = self.env['pharma.capa'].search_count([
                    ('deviation_id.batch_id', '=', rec.production_id.id),
                    ('status', 'in', ('draft', 'in_progress', 'under_review'))
                ])
                rec.no_open_capas = (open_capas == 0)
            else:
                rec.no_open_deviations = True
                rec.no_open_capas = True

            # Simple yield threshold check (e.g. >= 90%)
            expected = rec.production_id.product_qty or 1
            actual = rec.production_id.qty_producing or 0
            yield_pct = (actual / expected) * 100
            rec.yield_within_threshold = (yield_pct >= 90.0)

    @api.depends('bmr_completed', 'fg_qc_passed', 'no_open_deviations', 'no_open_capas', 'yield_within_threshold', 'all_bmr_steps_completed', 'all_ipqc_passed')
    def _compute_overall_status(self):
        """Executes the _compute_overall_status operation."""
        for rec in self:
            if all([
                rec.bmr_completed, rec.fg_qc_passed, rec.no_open_deviations,
                rec.no_open_capas, rec.yield_within_threshold, rec.all_bmr_steps_completed,
                rec.all_ipqc_passed
            ]):
                rec.overall_status = 'all_clear'
            else:
                rec.overall_status = 'pending'

    @api.depends('lot_id')
    def _compute_fg_qc(self):
        """Executes the _compute_fg_qc operation."""
        for rec in self:
            qc = self.env['pharma.qc.test.order'].search([
                ('lot_id', '=', rec.lot_id.id),
                ('stage', 'in', ('finished', 'finished_product'))
            ], limit=1, order="id desc")
            rec.fg_qc_test_id = qc.id
            rec.fg_qc_status = qc.status if qc else False
            rec.fg_qc_stage = qc.stage if qc else False
            rec.fg_qc_reviewed_by = qc.reviewed_by.id if qc else False

    @api.depends('production_id')
    def _compute_yield(self):
        """Executes the _compute_yield operation."""
        for rec in self:
            expected = rec.production_id.product_qty or 0.0
            actual = rec.production_id.qty_producing or 0.0
            # If we want them to display as % directly or units:
            rec.expected_yield = expected
            rec.actual_yield = actual
            if expected > 0:
                pct = (actual / expected)
            else:
                pct = 0.0
            rec.yield_percentage = pct
            rec.yield_flag = 'Within Limit' if pct >= 0.90 else 'Out of Limit'

    def action_view_bmr(self):
        """Executes the action_view_bmr operation."""
        self.ensure_one()
        return {
            'name': 'BMR',
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.bmr',
            'view_mode': 'list,form',
            'domain': [('production_id', '=', self.production_id.id)],
        }

    def action_view_qc_tests(self):
        """Executes the action_view_qc_tests operation."""
        self.ensure_one()
        lot_ids = self._batch_lot_ids()
        return {
            'name': 'QC Test Orders',
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
        """Executes the action_view_deviations operation."""
        self.ensure_one()
        # Deviations live in the optional pharma_capa_deviation module.
        if 'pharma.deviation' not in self.env:
            return False
        lot_ids = self._batch_lot_ids()
        return {
            'name': 'Deviations',
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.deviation',
            'view_mode': 'list,form',
            # Finished-batch deviations (batch_id) OR raw-material lot deviations
            # (lot_id on any consumed lot).
            'domain': ['|', ('batch_id', '=', self.production_id.id), ('lot_id', 'in', lot_ids.ids)],
        }

    def action_view_capas(self):
        """Executes the action_view_capas operation."""
        self.ensure_one()
        # CAPAs live in the optional pharma_capa_deviation module.
        if 'pharma.capa' not in self.env:
            return False
        lot_ids = self._batch_lot_ids()
        devs = self.env['pharma.deviation'].search([
            '|', ('batch_id', '=', self.production_id.id), ('lot_id', 'in', lot_ids.ids)
        ])
        return {
            'name': 'CAPAs',
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.capa',
            'view_mode': 'list,form',
            'domain': [('deviation_id', 'in', devs.ids)],
        }

    def action_view_coa(self):
        """Executes the action_view_coa operation."""
        self.ensure_one()
        return {
            'name': 'CoAs',
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.coa',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.lot_id.id)],
        }

    def action_view_genealogy(self):
        """Executes the action_view_genealogy operation."""
        self.ensure_one()
        if not self.lot_id:
            raise ValidationError("No Lot/Batch is linked to this QA Release record yet, so batch genealogy cannot be shown.")
        # Open the dedicated Batch Genealogy form (with the traceability
        # notebook) rather than the default stock.lot form, which does not
        # surface the genealogy details.
        return {
            'name': 'Batch Genealogy',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'form',
            'views': [(self.env.ref('pharma_traceability_coa.stock_lot_genealogy_form').id, 'form')],
            'res_id': self.lot_id.id,
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Executes the create operation."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('pharma.qa.release') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        """Executes the action_confirm operation."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            "Only QA can confirm and release a batch.",
        )
        for rec in self:
            if rec.state != 'draft':
                continue
            bmr = rec.production_id
            lot_ids = self.env['stock.lot']
            if rec.lot_id:
                lot_ids |= rec.lot_id
            if bmr:
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
                raise ValidationError("There are open OOS investigations for this batch. They must be closed before QA Release.")

            # Deviation gate — only enforced when the optional pharma_capa_deviation
            # module is installed (no deviations exist otherwise).
            if 'pharma.deviation' in self.env:
                open_deviations = self.env['pharma.deviation'].search_count([
                    ('batch_id', '=', bmr.id),
                    ('status', 'in', ('open', 'under_investigation'))
                ])
                if open_deviations > 0:
                    raise ValidationError("There are open or under investigation deviations for this batch. They must be resolved before QA Release.")

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
                    lines.append((0, 0, {
                        'parameter': res_line.parameter,
                        'expected_min': res_line.expected_min,
                        'expected_max': res_line.expected_max,
                        'actual_value': res_line.actual_value,
                        'uom': res_line.uom,
                        'status': mapped_status,
                    }))
            # Populate IPQC parameter check results into CoA line items as well
            for ipqc in rec.ipqc_ids:
                if ipqc.parameter_id:
                    mapped_status = 'pass' if ipqc.result == 'pass' else ('oos' if ipqc.result == 'fail' else 'pending')
                    lines.append((0, 0, {
                        'parameter': ipqc.parameter or ipqc.parameter_id.parameter_name,
                        'expected_min': ipqc.expected_min,
                        'expected_max': ipqc.expected_max,
                        'actual_value': ipqc.actual_value,
                        'uom': ipqc.parameter_id.uom_id.name if ipqc.parameter_id.uom_id else '',
                        'status': mapped_status,
                    }))
            coa_vals['coa_line_ids'] = lines

            # CoA (and its lines) are generated by the QA release; QA has no
            # create right, so this downstream record is created elevated.
            coa = self.env['pharma.coa'].sudo().create(coa_vals)
            rec.coa_id = coa.id
            rec.state = 'released'

            if rec.lot_id:
                rec.lot_id.write({'lot_status': 'released'})

            bmr.message_post(body=f"Batch released by QA. Certificate of Analysis {coa.name} has been generated.")
