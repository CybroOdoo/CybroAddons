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
import statistics

from odoo import api, fields, models
from odoo.exceptions import UserError

SPEC_STAGES = [
    ('incoming', 'Incoming / Raw Material'),
    ('finished', 'Finished Goods'),
    ('ipqc', 'IPQC'),
]

# Fields fixed by QA's approval of the normal range.
RANGE_FIELDS = {
    'range_mean', 'range_std_dev', 'range_sigma', 'range_low', 'range_high',
    'range_sample_count', 'range_approved_by', 'range_approved_on',
}


def parameter_key(name):
    """Normalised parameter name, so 'Assay ' and 'assay' share one history."""
    return ' '.join((name or '').split()).lower()


class PharmaTrendParameter(models.Model):
    """One watched product parameter at one site and its approved normal range.

    History is keyed by product, specification stage and parameter name, so it
    carries across specification versions. QA approves the normal range;
    from then on, results outside it are flagged on their test order. QA may
    re-approve it later from the results collected so far; the chatter keeps
    the history of the range.
    """
    _name = 'pharma.trend.parameter'
    _description = 'Trended Parameter'
    _inherit = ['mail.thread', 'pharma.workflow.mixin']
    _order = 'product_id, stage, parameter_name'

    name = fields.Char(
        compute='_compute_name',
        store=True,
        help='Product, parameter and testing stage.',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Site',
        required=True,
        readonly=True,
        index=True,
        default=lambda self: self.env.company,
        help='Site whose own results make up this history.',
    )
    product_id = fields.Many2one(
        comodel_name='product.template',
        required=True,
        readonly=True,
        index=True,
        ondelete='restrict',
        help='Product whose results are trended.',
    )
    stage = fields.Selection(
        selection=SPEC_STAGES,
        string='Testing Stage',
        required=True,
        readonly=True,
        help='Specification stage the parameter is tested at.',
    )
    parameter_name = fields.Char(
        string='Parameter',
        required=True,
        readonly=True,
        help='Name of the watched test parameter.',
    )
    parameter_key = fields.Char(
        required=True,
        readonly=True,
        index=True,
        help='Normalised parameter name the history is matched on.',
    )
    uom = fields.Char(
        string='UoM',
        readonly=True,
        help='Unit the results are reported in.',
    )
    spec_line_id = fields.Many2one(
        comodel_name='pharma.qc.spec.line',
        string='Specification Parameter',
        readonly=True,
        ondelete='set null',
        help='Parameter of the latest approved specification for this product and stage.',
    )
    is_trended = fields.Boolean(
        string='Watched',
        readonly=True,
        default=True,
        tracking=True,
        help='Whether the latest approved specification ticks this parameter.',
    )
    spec_min = fields.Float(
        string='Spec. Min',
        digits=(16, 4),
        readonly=True,
        help='Lower registered specification limit.',
    )
    spec_max = fields.Float(
        string='Spec. Max',
        digits=(16, 4),
        readonly=True,
        help='Upper registered specification limit.',
    )
    has_spec_min = fields.Boolean(
        string='Has Spec. Min',
        readonly=True,
        help='Whether the specification sets a lower limit.',
    )
    has_spec_max = fields.Boolean(
        string='Has Spec. Max',
        readonly=True,
        help='Whether the specification sets an upper limit.',
    )
    result_line_ids = fields.One2many(
        comodel_name='pharma.qc.result.line',
        inverse_name='trend_parameter_id',
        string='Results',
        help='Results of this parameter on every test order.',
    )
    state = fields.Selection(
        selection=[
            ('collecting', 'Collecting Results'),
            ('active', 'Normal Range Approved'),
        ],
        string='Status',
        compute='_compute_state',
        store=True,
        help='Collecting Results — no normal range approved yet; nothing is '
             'flagged. Normal Range Approved — results outside the range are '
             'flagged on their test order.',
    )
    range_mean = fields.Float(
        string='Mean', digits=(16, 4), readonly=True, tracking=True,
        help='Mean of the approved results the range was built from.')
    range_std_dev = fields.Float(
        string='Std. Deviation', digits=(16, 4), readonly=True,
        help='Sample standard deviation of those results.')
    range_sigma = fields.Float(
        string='Width (σ)', readonly=True,
        help='Standard deviations either side of the mean.')
    range_low = fields.Float(
        string='Normal Range Low', digits=(16, 4), readonly=True, tracking=True,
        help='Lower end of the normal range, never below the specification minimum.')
    range_high = fields.Float(
        string='Normal Range High', digits=(16, 4), readonly=True, tracking=True,
        help='Upper end of the normal range, never above the specification maximum.')
    range_sample_count = fields.Integer(
        string='Results Used', readonly=True,
        help='Number of approved results the range was built from.')
    range_approved_by = fields.Many2one(
        comodel_name='res.users', string='Approved By', readonly=True, tracking=True,
        help='QA user who approved the normal range.')
    range_approved_on = fields.Datetime(
        string='Approved On', readonly=True, tracking=True,
        help='When the normal range was approved.')
    result_count = fields.Integer(
        string='Approved Results',
        compute='_compute_result_count',
        help='Results of passed test orders in the history.',
    )
    min_history = fields.Integer(
        string='Results Needed',
        compute='_compute_result_count',
        help='Approved results needed before the normal range can be approved.',
    )
    flagged_count = fields.Integer(
        string='Outside Normal Range',
        compute='_compute_result_count',
        help='Results flagged outside the normal range.',
    )

    _unique_trend_key = models.Constraint(
        'UNIQUE(company_id, product_id, stage, parameter_key)',
        'This parameter is already watched for this product, stage and site.',
    )

    @api.depends('product_id', 'parameter_name', 'stage')
    def _compute_name(self):
        """Product / parameter (stage)."""
        stages = dict(SPEC_STAGES)
        for rec in self:
            rec.name = '%s / %s (%s)' % (
                rec.product_id.name or '', rec.parameter_name or '',
                stages.get(rec.stage, ''))

    @api.depends('range_approved_on')
    def _compute_state(self):
        """Flagging runs only against an approved range."""
        for rec in self:
            rec.state = 'active' if rec.range_approved_on else 'collecting'

    def _compute_result_count(self):
        """Counts shown on the form and list."""
        for rec in self:
            rec.result_count = len(rec._approved_results())
            rec.min_history = rec.company_id._pharma_trend_settings()['pharma_trend_min_history']
            rec.flagged_count = len(rec.result_line_ids.filtered('outside_normal_range'))

    def write(self, vals):
        """The normal range changes only through QA (re-)approval."""
        if RANGE_FIELDS.intersection(vals) and not self.env.context.get('pharma_trend_approve'):
            raise UserError(self.env._('The normal range is set only by QA approval.'))
        return super().write(vals)

    # ------------------------------------------------------------------
    # Creation and specification link
    # ------------------------------------------------------------------
    @api.model
    def _pharma_get_or_create(self, spec_line, company):
        """The watched parameter for a specification line at a site, created on first use."""
        spec = spec_line.spec_id
        key = parameter_key(spec_line.parameter_name)
        param = self.sudo().search([
            ('company_id', '=', company.id),
            ('product_id', '=', spec.product_id.id),
            ('stage', '=', spec.stage),
            ('parameter_key', '=', key),
        ], limit=1)
        if not param:
            param = self.sudo().create({
                'company_id': company.id,
                'product_id': spec.product_id.id,
                'stage': spec.stage,
                'parameter_name': spec_line.parameter_name.strip(),
                'parameter_key': key,
            })
            param._pharma_sync_spec_line(spec_line)
        return param

    def _pharma_sync_spec_line(self, spec_line):
        """Take the registered limits and the watch tick from an approved specification line."""
        for rec in self.sudo():
            rec.write({
                'spec_line_id': spec_line.id,
                'is_trended': spec_line.is_trended,
                'uom': spec_line.uom_id.name or rec.uom or '',
                'spec_min': spec_line.min_value,
                'spec_max': spec_line.max_value,
                'has_spec_min': spec_line.min_value != 0.0,
                'has_spec_max': spec_line.max_value != 0.0,
            })

    # ------------------------------------------------------------------
    # History and range
    # ------------------------------------------------------------------
    def _approved_results(self, limit=None):
        """Entered results of passed test orders, oldest first (the last ``limit`` if given)."""
        self.ensure_one()
        lines = self.env['pharma.qc.result.line'].sudo().search([
            ('trend_parameter_id', '=', self.id),
            ('result_entered', '=', True),
            ('test_order_id.status', '=', 'passed'),
        ], order='id desc', limit=limit)
        return lines[::-1]

    def _pharma_is_outside(self, value):
        """Whether a value lies outside the approved normal range."""
        self.ensure_one()
        return self.state == 'active' and not self.range_low <= value <= self.range_high

    def action_approve_range(self):
        """Approve the normal range from the approved results collected so far.

        A range already in force can be re-approved from the results collected
        since. Results evaluated under the old range keep their flag; only
        results on orders still under test are compared with the new one.
        """
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            self.env._('Only QA can approve a normal range.'),
        )
        # Evaluate any result still pending against the range in force now,
        # before that range moves.
        self.env['pharma.qc.result.line'].flush_model([
            'outside_normal_range', 'normal_range_applied',
            'normal_range_low', 'normal_range_high'])
        for rec in self:
            settings = rec.company_id._pharma_trend_settings()
            values = rec._approved_results().mapped('actual_value')
            if len(values) < settings['pharma_trend_min_history']:
                raise UserError(self.env._(
                    '%(param)s has %(count)s approved results; %(min)s are needed '
                    'before the normal range can be approved.',
                    param=rec.name, count=len(values),
                    min=settings['pharma_trend_min_history']))
            mean = statistics.fmean(values)
            std = statistics.stdev(values)
            if std <= 0:
                raise UserError(self.env._(
                    'The results of %s show no variation, so no meaningful range '
                    'can be set. Check the reported precision of the results.', rec.name))
            k = settings['pharma_trend_range_sigma']
            low, high = mean - k * std, mean + k * std
            # The normal range always sits inside the specification.
            if rec.has_spec_min:
                low = max(low, rec.spec_min)
            if rec.has_spec_max:
                high = min(high, rec.spec_max)
            previous = rec.state == 'active' and {
                'low': rec.range_low,
                'high': rec.range_high,
                'mean': rec.range_mean,
                'k': rec.range_sigma,
                'count': rec.range_sample_count,
                'user': rec.range_approved_by.name or '',
                'on': rec.range_approved_on,
            }
            now = fields.Datetime.now()
            rec.sudo().with_context(pharma_trend_approve=True).write({
                'range_mean': mean,
                'range_std_dev': std,
                'range_sigma': k,
                'range_low': low,
                'range_high': high,
                'range_sample_count': len(values),
                'range_approved_by': self.env.user.id,
                'range_approved_on': now,
            })
            # Only results entered on orders still under test are compared with
            # the new range; closed results keep the flag of the range they met.
            open_lines = rec.result_line_ids.filtered(
                lambda line: line.result_entered
                and line.test_order_id.status in ('in_progress', 'under_investigation'))
            for fname in ('outside_normal_range', 'normal_range_applied',
                          'normal_range_low', 'normal_range_high'):
                self.env.add_to_compute(open_lines._fields[fname], open_lines)
            orders = open_lines.test_order_id
            self.env.add_to_compute(orders._fields['outside_normal_range'], orders)
            rec.message_post(body=rec._pharma_range_message(
                previous, low, high, mean, k, len(values), now))

    def _pharma_range_message(self, previous, low, high, mean, k, count, when):
        """Chatter entry for an approval, naming what changed for a re-approval."""
        self.ensure_one()
        on = fields.Datetime.to_string(fields.Datetime.context_timestamp(self, when))
        if not previous:
            return self.env._(
                'Normal range approved by %(user)s on %(on)s: %(low).4f – %(high).4f '
                '(mean %(mean).4f ± %(k)s σ, built from %(count)s results).',
                user=self.env.user.name, on=on, low=low, high=high, mean=mean,
                k=k, count=count)
        prev_on = fields.Datetime.to_string(
            fields.Datetime.context_timestamp(self, previous['on'])) if previous['on'] else ''
        return self.env._(
            'Normal range re-approved by %(user)s on %(on)s. '
            'Old range: %(old_low).4f – %(old_high).4f (mean %(old_mean).4f ± %(old_k)s σ, '
            'built from %(old_count)s results, approved by %(old_user)s on %(old_on)s). '
            'New range: %(low).4f – %(high).4f (mean %(mean).4f ± %(k)s σ, built from '
            '%(count)s results). Results already evaluated keep the flag of the old '
            'range; only orders still under test are checked against the new one.',
            user=self.env.user.name, on=on,
            old_low=previous['low'], old_high=previous['high'],
            old_mean=previous['mean'], old_k=previous['k'],
            old_count=previous['count'], old_user=previous['user'], old_on=prev_on,
            low=low, high=high, mean=mean, k=k, count=count)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_open_chart(self):
        """Open the trend chart of this parameter."""
        self.ensure_one()
        return {
            'name': self.env._('Trend Chart — %s', self.name),
            'type': 'ir.actions.client',
            'tag': 'pharma_trend_control_chart',
            'params': {'trend_parameter_id': self.id},
        }

    def action_open_apqr_export(self):
        """Open the APQR trending export for this parameter's product."""
        self.ensure_one()
        return {
            'name': self.env._('APQR Trending Export'),
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.trend.apqr.export',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.product_id.id,
                'default_company_id': self.company_id.id,
            },
        }

    def action_view_flagged_orders(self):
        """Open the test orders with a result of this parameter outside the normal range."""
        self.ensure_one()
        return {
            'name': self.env._('Outside Normal Range'),
            'type': 'ir.actions.act_window',
            'res_model': 'pharma.qc.test.order',
            'view_mode': 'list,form',
            'domain': [('result_line_ids', 'any', [
                ('trend_parameter_id', '=', self.id), ('outside_normal_range', '=', True)])],
            'context': {'create': False},
        }

    def get_chart_data(self, limit=60):
        """Recent approved results and the normal range for the chart client action."""
        self.ensure_one()
        lines = self._approved_results(limit=limit or None)
        return {
            'name': self.name,
            'uom': self.uom or '',
            'state': self.state,
            'result_count': self.result_count,
            'min_history': self.min_history,
            'points': [{
                'order_id': line.test_order_id.id,
                'lot': line.test_order_id.lot_id.name or line.test_order_id.name or '',
                'date': fields.Datetime.to_string(line.test_order_id.create_date),
                'value': line.actual_value,
                'outside': line.outside_normal_range,
            } for line in lines],
            'range': {
                'low': self.range_low,
                'high': self.range_high,
                'mean': self.range_mean,
                'approved_on': fields.Date.to_string(self.range_approved_on.date()),
            } if self.state == 'active' else False,
            'spec': {
                'min': self.spec_min if self.has_spec_min else False,
                'max': self.spec_max if self.has_spec_max else False,
            },
        }

    def _pharma_report_stats(self):
        """Summary statistics of the approved results for the trend summary report."""
        self.ensure_one()
        lines = self._approved_results()
        values = lines.mapped('actual_value')
        return {
            'lines': lines,
            'count': len(values),
            'mean': statistics.fmean(values) if values else 0.0,
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0,
            'min': min(values) if values else 0.0,
            'max': max(values) if values else 0.0,
            'flagged': len(lines.filtered('outside_normal_range')),
        }
