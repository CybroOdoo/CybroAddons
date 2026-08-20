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


class MrpProduction(models.Model):
    """Extends MRP Production with BMR and QA Release workflows."""
    _inherit = 'mrp.production'

    bmr_ids = fields.One2many(
        comodel_name='pharma.bmr',
        inverse_name='production_id',
        string='Batch Manufacturing Records',
        help='Specifies the Batch Manufacturing Records for this record.',
    )
    bmr_count = fields.Integer(
        string='BMR Count',
        compute='_compute_bmr_count',
        help='Specifies the BMR Count for this record.',
    )
    pharma_bmr_completed = fields.Boolean(
        string='BMR Completed',
        compute='_compute_pharma_bmr_completed',
        help='Specifies the BMR Completed for this record.',
    )
    pharma_allowed_component_ids = fields.Many2many(help='Specifies the Pharma Allowed Component Ids for this record.',
        comodel_name='product.product',
        compute='_compute_pharma_allowed_component_ids',
        string='Allowed Components'
    )
    qc_test_order_count = fields.Integer(
        string='QC Test Orders',
        compute='_compute_qc_test_order_count',
        help='Specifies the number of QC Test Orders linked to this order.',
    )
    qa_release_eligible = fields.Boolean(
        string='Ready for QA Release',
        compute='_compute_qa_release_eligible',
        search='_search_qa_release_eligible',
        help='True when the batch has reached the end of the core workflow — the '
             'BMR is completed and finished-goods QC has passed (on a non-cancelled '
             'MO) — so it is ready to be sent to QA Release (optional traceability tier).'
    )
    pharma_qa_release_exists = fields.Boolean(
        string='QA Release Created',
        compute='_compute_pharma_qa_release_exists',
        help='True when a QA Release Queue record already exists for this batch. '
             'Always False unless the optional traceability tier is installed.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Executes the create operation."""
        records = super().create(vals_list)
        records._merge_identical_lines()
        return records

    def write(self, vals):
        """Executes the write operation."""
        res = super().write(vals)
        if 'move_raw_ids' in vals:
            self._merge_identical_lines()
        return res

    def _merge_identical_lines(self):
        """Merges identical product lines into a single line with summed quantities."""
        for mo in self:
            if mo.state not in ['draft', 'confirmed']:
                continue
            seen = {}
            moves_to_unlink = self.env['stock.move']
            for move in mo.move_raw_ids:
                if not move.product_id:
                    continue
                key = (move.product_id.id, move.product_uom.id)
                if key in seen:
                    seen[key].product_uom_qty += move.product_uom_qty
                    moves_to_unlink |= move
                else:
                    seen[key] = move
            if moves_to_unlink:
                if mo.state == 'confirmed':
                    moves_to_unlink._action_cancel()
                moves_to_unlink.unlink()

    @api.depends('bmr_ids')
    def _compute_bmr_count(self):
        """Count the Batch Manufacturing Records linked to this manufacturing order."""
        for rec in self:
            rec.bmr_count = len(rec.bmr_ids)

    @api.depends('bmr_ids.status')
    def _compute_pharma_bmr_completed(self):
        """Executes the _compute_pharma_bmr_completed operation."""
        for rec in self:
            if rec.bmr_ids:
                rec.pharma_bmr_completed = all(b.status == 'completed' for b in rec.bmr_ids)
            else:
                rec.pharma_bmr_completed = False

    @api.depends('bom_id', 'bom_id.bom_line_ids.product_id')
    def _compute_pharma_allowed_component_ids(self):
        """Executes the _compute_pharma_allowed_component_ids operation."""
        for rec in self:
            if rec.bom_id:
                rec.pharma_allowed_component_ids = rec.bom_id.bom_line_ids.mapped('product_id')
            else:
                rec.pharma_allowed_component_ids = self.env['product.product']

    def button_mark_done(self):
        """Executes the button_mark_done operation."""
        for rec in self:
            if not rec.pharma_bmr_completed:
                raise UserError(_("Cannot produce: The linked Batch Manufacturing Record (BMR) must be completed first."))
        return super(MrpProduction, self).button_mark_done()

    def action_confirm(self):
        # Enforce that only approved formulas (BoMs) can be used to confirm a production order
        """Enforce approved BoM usage and auto-generate the BMR on confirmation."""
        for rec in self:
            if rec.bom_id and rec.bom_id.formula_status not in ('done', 'approved'):
                raise UserError(_(
                    'Cannot confirm Manufacturing Order %s because BoM/Formula "%s" is not Approved.'
                ) % (rec.name, rec.bom_id.display_name))
            if rec.all_move_raw_ids:
                for record in rec.all_move_raw_ids:
                    if record.qc_test_order_status != 'pass':
                        raise UserError(_('Please check QC Test Order'))

        res = super(MrpProduction, self).action_confirm()

        # Auto-create BMR
        for rec in self:
            if not rec.bmr_ids:
                rec.action_create_bmr()
        return res

    def action_create_bmr(self):
        """Generate a Draft BMR with steps and IPQC parameters from the BoM."""
        self.ensure_one()
        if self.bmr_ids:
            raise UserError(_('A BMR already exists for this Manufacturing Order.'))

        # Expected yield calculation
        expected_yield = self.product_qty
        if self.bom_id and self.bom_id.theoretical_yield:
            expected_yield = self.product_qty * (self.bom_id.theoretical_yield / 100.0)

        # Batch number: use lot_producing_ids if set, otherwise default to MO name
        batch_no = self.lot_producing_ids[0].name if self.lot_producing_ids else self.name

        # Create BMR
        bmr = self.env['pharma.bmr'].create({
            'production_id': self.id,
            'product_id': self.product_id.product_tmpl_id.id,
            'batch_no': batch_no,
            'yield_expected': expected_yield,
            'status': 'draft',
        })

        # Pull steps from BOM operations
        if self.bom_id and self.bom_id.operation_ids:
            for op in self.bom_id.operation_ids:
                self.env['pharma.bmr.step'].create({
                    'bmr_id': bmr.id,
                    'sequence': op.sequence,
                    'description': op.name,
                    'status': 'pending',
                })
        else:
            # Create a default step if BOM has no operations
            self.env['pharma.bmr.step'].create({
                'bmr_id': bmr.id,
                'sequence': 10,
                'description': _('Standard Manufacturing Execution Step'),
                'status': 'pending',
            })

        # Pull IPQC parameters from approved inprocess QC Spec
        qc_spec = self.env['pharma.qc.spec'].search([
            ('product_id', '=', self.product_id.product_tmpl_id.id),
            ('stage', '=', 'inprocess'),
            ('state', '=', 'approved'),
        ], limit=1)
        if qc_spec:
            for line in qc_spec.parameter_ids:
                self.env['pharma.ipqc.result'].create({
                    'bmr_id': bmr.id,
                    'parameter_id': line.id,
                    'expected_min': line.min_value,
                    'expected_max': line.max_value,
                })

        return bmr

    def _pharma_raw_material_lots(self):
        """Raw-material lots consumed by this MO, inferred from its BOM components."""
        self.ensure_one()
        lot_ids = self.env['stock.lot']
        # Lots actually recorded as consumed on the component moves (present
        # when consumption is done through the normal flow).
        lot_ids |= self.move_raw_ids.mapped('move_line_ids.lot_id')
        # Inferred received lots of the component products.
        component_products = self.move_raw_ids.mapped('product_id')
        if component_products:
            incoming_qc = self.env['pharma.qc.test.order'].search([
                ('stage', '=', 'incoming'),
                ('lot_id', '!=', False),
                ('lot_id.product_id', 'in', component_products.ids),
            ])
            lot_ids |= incoming_qc.mapped('lot_id')
        return lot_ids

    def _qc_test_order_domain(self):
        """Domain of QC Test Orders for this MO's produced and consumed lots."""
        self.ensure_one()
        lot_ids = self.env['stock.lot']
        lot_ids |= self.lot_producing_ids
        lot_ids |= self._pharma_raw_material_lots()
        return [('lot_id', 'in', lot_ids.ids)]

    @api.depends('lot_producing_ids', 'move_raw_ids.move_line_ids.lot_id')
    def _compute_qc_test_order_count(self):
        """Executes the _compute_qc_test_order_count operation."""
        for rec in self:
            rec.qc_test_order_count = self.env['pharma.qc.test.order'].search_count(
                rec._qc_test_order_domain())

    def action_view_qc_test_orders(self):
        """Open the QC Test Orders for this MO's produced and consumed lots."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'pharmaceutical_base.pharma_qc_test_order')
        domain = self._qc_test_order_domain()
        action['domain'] = domain
        orders = self.env['pharma.qc.test.order'].search(domain)
        if len(orders) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = orders.id
        return action

    def action_view_bmr(self):
        """Open the BMR form/list for this MO."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('pharmaceutical_base.pharma_bmr_action')
        # Prevent manual BMR creation from the Production Order
        context_str = action.get('context', '{}')
        from ast import literal_eval
        try:
            ctx = literal_eval(context_str) if isinstance(context_str, str) else (context_str or {})
        except Exception:
            ctx = {}
        ctx['create'] = False
        action['context'] = ctx
        if len(self.bmr_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.bmr_ids[0].id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('production_id', '=', self.id)],
            })
        return action

    @api.depends('state', 'pharma_bmr_completed',
                 'lot_producing_ids', 'lot_producing_ids.lot_status')
    def _compute_qa_release_eligible(self):
        """Flag whether the batch is ready for QA Release."""
        release_enabled = 'pharma.qa.release' in self.env
        for bmr in self:
            if not release_enabled:
                bmr.qa_release_eligible = False
                continue
            fg_qc = self.env['pharma.qc.test.order'].search([
                ('lot_id', 'in', bmr.lot_producing_ids.ids),
                ('stage', 'in', ('finished', 'finished_product')),
            ])
            fg_qc_passed = bool(fg_qc) and all(t.status == 'passed' for t in fg_qc)
            bmr.qa_release_eligible = bool(
                bmr.state not in ('draft', 'cancel')
                and bmr.pharma_bmr_completed and fg_qc_passed)

    def _search_qa_release_eligible(self, operator, value):
        """Search manufacturing orders eligible for QA Release."""
        if 'pharma.qa.release' not in self.env:
            # Tier disabled → no batch is ever eligible for QA release.
            wants_eligible = (operator == '=' and value) or (operator == '!=' and not value)
            return [('id', 'in', [])] if wants_eligible else []
        eligible_domain = [('state', 'not in', ('draft', 'cancel'))]
        not_eligible_domain = [('state', 'in', ('draft', 'cancel'))]
        if operator == '=' and value is True:
            return eligible_domain
        elif operator == '!=' and value is True:
            return not_eligible_domain
        elif operator == '=' and value is False:
            return not_eligible_domain
        elif operator == '!=' and value is False:
            return eligible_domain
        return [('id', 'in', [])]

    def _compute_pharma_qa_release_exists(self):
        """Flag batches already sent to QA Release when the tier is installed."""
        for rec in self:
            if 'pharma.qa.release' in self.env:
                rec.pharma_qa_release_exists = self.env['pharma.qa.release'].search_count(
                    [('production_id', '=', rec.id)]) > 0
            else:
                rec.pharma_qa_release_exists = False

    def action_qa_release(self):
        """Placeholder QA Release action; overridden by the traceability module."""
        raise UserError(_(
            "QA Release requires the 'Traceability, CoA & Audit Trail' feature. "
            "Enable it in the Pharmaceutical ERP settings."))
