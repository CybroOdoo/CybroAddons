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

# Default number of cycles offered for each trigger.
_DEFAULT_CYCLES = {
    'batch': 5,
    'time': 2,
}


class PharmaCapa(models.Model):
    """Corrective and Preventive Action (CAPA)."""
    _name = 'pharma.capa'
    _description = 'Corrective and Preventive Action (CAPA)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='CAPA Number',
        default='New',
        copy=False,
        readonly=True,
        tracking=True,
        help='Specifies the CAPA Number for this record.',
    )
    deviation_id = fields.Many2one(
        comodel_name='pharma.deviation',
        string='Source Deviation',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
        help='No standalone CAPAs — every CAPA must originate from a deviation.',
    )
    deviation_count = fields.Integer(help='Specifies the Deviation Count for this record.',
        compute='_compute_deviation_count',
    )
    capa_type = fields.Selection(
        selection=[
            ('corrective', 'Corrective'),
            ('preventive', 'Preventive'),
        ],
        string='CAPA Type',
        required=True,
        default='corrective',
        tracking=True,
        help='Specifies the CAPA Type for this record.',
    )
    root_cause = fields.Text(
        compute='_compute_root_cause',
        store=True,
        readonly=False,
        help='Taken from the source deviation. Edit it here to override for '
             'this CAPA; clear it to follow the deviation again.',
    )
    root_cause_overridden = fields.Boolean(
        copy=False,
        tracking=True,
        help='Set when the root cause on this CAPA has been edited away from '
             'the one recorded on the source deviation.',
    )
    action_plan = fields.Text(
        help='What will be done, by whom, and by when. Required for a '
             'corrective action; a preventive plan is its scope and schedule.',
    )
    plan_summary = fields.Char(
        string='Plan',
        compute='_compute_plan_summary',
        help='The preventive plan, derived from the scope and the schedule.',
    )
    effectiveness_check = fields.Text(
        compute='_compute_effectiveness_check',
        help='Cycles completed, findings raised and deviations opened, drawn '
             'from the checks themselves.',
    )
    effectiveness_conclusion = fields.Char(
        string='QA Conclusion',
        tracking=True,
        help='One line from QA stating whether the action was effective. '
             'Required to verify the CAPA.',
    )
    assigned_to = fields.Many2one(
        comodel_name='res.users',
        required=True,
        tracking=True,
        help='Specifies the Assigned To for this record.',
    )
    due_date = fields.Date(
        tracking=True,
        help='Specifies the Due Date for this record.',
    )
    status = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('verified', 'Verified'),
            ('closed', 'Closed'),
        ],
        default='open',
        required=True,
        copy=False,
        tracking=True,
        help='Specifies the Status for this record.',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.company,
        help='Site this CAPA belongs to — used to resolve site-wide scope.',
    )
    # ------------------------------------------------------------------
    # Preventive action — scope
    # ------------------------------------------------------------------
    # Tested material is in scope when it satisfies every field that has been
    # filled.
    # Entries within a field are alternatives; the fields combine. All three
    # empty means site-wide.
    scope_product_ids = fields.Many2many(
        comodel_name='product.template',
        relation='pharma_capa_scope_product_rel',
        column1='capa_id',
        column2='product_tmpl_id',
        string='Products',
        tracking=True,
        help='Tests on any of these products — or on batches making or '
             'consuming them — are in scope. Leave empty to cover every '
             'product.',
    )
    scope_location_ids = fields.Many2many(
        comodel_name='stock.location',
        relation='pharma_capa_scope_location_rel',
        column1='capa_id',
        column2='location_id',
        string='Locations',
        domain="[('usage', '=', 'internal')]",
        tracking=True,
        help='Tests on material held in, or batches drawing from or producing '
             'into, any of these locations (or their sub-locations) are in '
             'scope. Leave empty to cover every location.',
    )
    scope_workcenter_ids = fields.Many2many(
        comodel_name='mrp.workcenter',
        relation='pharma_capa_scope_workcenter_rel',
        column1='capa_id',
        column2='workcenter_id',
        string='Workcenters',
        tracking=True,
        help='Tests on batches with an operation on any of these work centres '
             'are in scope. Leave empty to cover every line.',
    )
    scope_site_wide = fields.Boolean(
        string='Site-Wide',
        compute='_compute_scope_site_wide',
        store=True,
        help='No product, location or workcenter is named, so every test at '
             'the site is in scope.',
    )
    scope_summary = fields.Char(
        compute='_compute_scope_summary',
        help='The reach of the action as one readable line.',
    )
    # ------------------------------------------------------------------
    # Preventive action — schedule
    # ------------------------------------------------------------------
    trigger_type = fields.Selection(
        selection=[
            ('time', 'By Time'),
            ('batch', 'By Test'),
        ],
        string='Check Trigger',
        tracking=True,
        help='By time for a continuous risk (a quarterly audit); by test for '
             'the next several completed tests — incoming, in-process (IPQC) '
             'or finished goods — on material in scope.',
    )
    interval_count = fields.Integer(
        string='Every',
        default=3,
        help='Length of the interval between time-triggered checks.',
    )
    interval_uom = fields.Selection(
        selection=[
            ('day', 'Days'),
            ('week', 'Weeks'),
            ('month', 'Months'),
            ('year', 'Years'),
        ],
        string='Interval Unit',
        default='month',
        help='Specifies the Interval Unit for this record.',
    )
    cycle_count = fields.Integer(
        string='Tests to Observe',
        default=_DEFAULT_CYCLES['batch'],
        help='How many checks a campaign runs before it finishes. For a test '
             'trigger, each completed test on material in scope is one; for a '
             'time trigger, each interval is one.',
    )
    backstop_date = fields.Date(
        tracking=True,
        help='Five tests or twelve months, whichever comes first. Without '
             'this a material that is never tested leaves the CAPA open '
             'indefinitely.',
    )
    # ------------------------------------------------------------------
    # Preventive action — nature of the control
    # ------------------------------------------------------------------
    control_nature = fields.Selection(
        selection=[
            ('campaign', 'Campaign — runs a set number of times'),
            ('permanent', 'Permanent control — continues indefinitely'),
        ],
        tracking=True,
        help='A campaign finishes on its own. A permanent control continues '
             'after the CAPA closes and must be reviewed periodically.',
    )
    review_interval_months = fields.Integer(
        string='Review Every (Months)',
        default=12,
        help='How often a permanent control is reviewed to decide whether it '
             'remains warranted.',
    )
    review_date = fields.Date(
        string='Next Review Date',
        tracking=True,
        help='Specifies the Next Review Date for this record.',
    )
    handover_owner_id = fields.Many2one(
        comodel_name='res.users',
        string='Control Owner After Closure',
        tracking=True,
        help='Department owner who runs the permanent control as routine '
             'operations once the CAPA has closed.',
    )
    handover_notes = fields.Text(
        help='How the control is run once it leaves the CAPA.',
    )
    preventive_managed = fields.Boolean(
        string='Preventive Action Applies',
        compute='_compute_preventive_managed',
        help='A preventive CAPA whose plan is run by the Preventive Action '
             'add-on: recurring checks, schedule and effectiveness.',
    )
    preventive_premium_locked = fields.Boolean(
        string='Preventive Action Not Enabled',
        compute='_compute_preventive_managed',
        help='A preventive CAPA without the Preventive Action add-on: it is '
             'recorded with an action plan.',
    )
    closed_by = fields.Many2one(
        comodel_name='res.users',
        copy=False,
        readonly=True,
        tracking=True,
        help='QA Director who closed after verifying effectiveness.',
    )
    closed_on = fields.Datetime(
        copy=False,
        readonly=True,
        tracking=True,
        help='Specifies the Closed On for this record.',
    )

    def _compute_deviation_count(self):
        """Executes the _compute_deviation_count operation."""
        for rec in self:
            rec.deviation_count = 1 if rec.deviation_id else 0

    @api.depends('deviation_id.root_cause', 'root_cause_overridden')
    def _compute_root_cause(self):
        """Follow the source deviation's root cause unless overridden here."""
        for rec in self:
            if not rec.root_cause_overridden:
                rec.root_cause = rec.deviation_id.root_cause

    @api.depends('capa_type', 'scope_product_ids', 'scope_location_ids',
                 'scope_workcenter_ids')
    def _compute_scope_site_wide(self):
        """Flag a preventive action whose scope names nothing."""
        for rec in self:
            rec.scope_site_wide = bool(
                rec.capa_type == 'preventive'
                and not rec.scope_product_ids
                and not rec.scope_location_ids
                and not rec.scope_workcenter_ids
            )

    @api.depends('scope_site_wide', 'scope_product_ids',
                 'scope_location_ids', 'scope_workcenter_ids', 'company_id')
    def _compute_scope_summary(self):
        """Render the reach of the action as one readable line."""
        for rec in self:
            if rec.capa_type != 'preventive':
                rec.scope_summary = ''
            elif rec.scope_site_wide:
                rec.scope_summary = self.env._(
                    'Site-wide — every test at %s',
                    rec.company_id.display_name or self.env._('this site'))
            else:
                if rec.scope_product_ids:
                    what = self.env._(
                        'on %s, or on batches making or consuming it,',
                        self.env._(' or ').join(
                            rec.scope_product_ids.mapped('display_name')))
                else:
                    what = self.env._('on any material')
                parts = [self.env._('Tests'), what]
                if rec.scope_workcenter_ids:
                    parts.append(self.env._('on %s', self.env._(' or ').join(
                        rec.scope_workcenter_ids.mapped('display_name'))))
                if rec.scope_location_ids:
                    parts.append(self.env._('at %s', self.env._(' or ').join(
                        rec.scope_location_ids.mapped('display_name'))))
                rec.scope_summary = ' '.join(parts).rstrip(',')

    @api.depends('capa_type', 'scope_summary', 'trigger_type', 'cycle_count',
                 'interval_count', 'interval_uom', 'backstop_date',
                 'control_nature')
    def _compute_plan_summary(self):
        """Show the preventive plan as scope plus schedule."""
        for rec in self:
            if rec.capa_type != 'preventive':
                rec.plan_summary = ''
                continue
            rec.plan_summary = self.env._(
                '%(scope)s; check %(schedule)s.',
                scope=rec.scope_summary,
                schedule=rec._schedule_summary() or self.env._('not yet scheduled'),
            )

    @api.depends('capa_type')
    def _compute_preventive_managed(self):
        """Without the Preventive Action add-on no plan is run: a preventive
        CAPA is recorded with an action plan, like a corrective one."""
        for rec in self:
            rec.preventive_managed = False
            rec.preventive_premium_locked = rec.capa_type == 'preventive'

    @api.depends('capa_type')
    def _compute_effectiveness_check(self):
        """Point QA to the conclusion; the Preventive Action add-on
        summarises its checks here instead."""
        for rec in self:
            rec.effectiveness_check = self.env._(
                'No recurring checks. State the evidence of effectiveness in '
                'the QA conclusion.')

    # ------------------------------------------------------------------
    # Preventive schedule
    # ------------------------------------------------------------------
    @api.onchange('capa_type')
    def _onchange_capa_type(self):
        """Offer sensible preventive defaults; clear them for a corrective."""
        if self.preventive_managed:
            product = self.deviation_id._pharma_scope_product() \
                if self.deviation_id else self.env['product.template']
            if not self.scope_product_ids and product:
                self.scope_product_ids = product
            if not self.trigger_type:
                self.trigger_type = 'batch' if product else 'time'
            if not self.control_nature:
                self.control_nature = 'campaign'
        else:
            self.scope_product_ids = False
            self.scope_location_ids = False
            self.scope_workcenter_ids = False
            self.trigger_type = False
            self.control_nature = False

    @api.onchange('trigger_type')
    def _onchange_trigger_type(self):
        """A test trigger is always a campaign; offer the usual count."""
        if self.trigger_type == 'batch':
            self.control_nature = 'campaign'
        if self.trigger_type in _DEFAULT_CYCLES:
            self.cycle_count = _DEFAULT_CYCLES[self.trigger_type]

    @api.constrains('capa_type', 'trigger_type', 'control_nature')
    def _check_batch_trigger_campaign(self):
        """A test-triggered action observes a set number of tests, then ends."""
        for rec in self:
            if rec.capa_type == 'preventive' and rec.trigger_type == 'batch' \
                    and rec.control_nature == 'permanent':
                raise ValidationError(self.env._(
                    'A test-triggered preventive action is a campaign over a '
                    'set number of tests. A control that continues '
                    'indefinitely is triggered by time.'))

    def action_view_deviation(self):
        """Executes the action_view_deviation operation."""
        self.ensure_one()
        return {
            'name': 'Source Deviation',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pharma.deviation',
            'res_id': self.deviation_id.id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Overrides creation to auto-assign a sequential CAPA number."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('pharma.capa') or 'New'
                )
        return super().create(vals_list)

    def action_start(self):
        """Move the CAPA from Open to In Progress."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            self.env._('Only QA can start a CAPA.'),
        )
        locked = self.filtered('preventive_premium_locked')
        if locked and not self.env.context.get('pharma_preventive_acknowledged'):
            # Without the Preventive Action add-on a preventive CAPA runs on
            # its action plan; say so before starting, from the feature dialog.
            return locked._pharma_open_preventive_start_dialog()
        for rec in self:
            if rec.status != 'open':
                raise UserError(self.env._('Only Open CAPAs can be started.'))
            rec._pharma_check_can_start()
            rec.status = 'in_progress'
            rec.message_post(body=self.env._('CAPA started by %s.', self.env.user.name))
            rec._pharma_after_start()

    def _pharma_check_can_start(self):
        """Hook: raise when this CAPA may not start yet."""
        self.ensure_one()

    def _pharma_after_start(self):
        """Hook: act on a CAPA that has just started."""
        self.ensure_one()

    def _pharma_open_preventive_start_dialog(self):
        """Open the Preventive Action dialog, offering to start these CAPAs
        with their action plan."""
        action = self.env.ref(
            'pharma_capa_deviation.pharma_premium_feature_capa_preventive'
        ).action_open_dialog()
        action['context'] = {'pharma_capa_start_ids': self.ids}
        return action

    def action_open_preventive_feature(self):
        """Describe the Preventive Action add-on."""
        return self.env.ref(
            'pharma_capa_deviation.pharma_premium_feature_capa_preventive'
        ).action_open_dialog()

    def action_follow_deviation_root_cause(self):
        """Drop the override and take the root cause from the deviation."""
        self.write({'root_cause_overridden': False})

    def action_verify(self):
        """Mark the CAPA Verified once effectiveness evidence is recorded."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            self.env._('Only QA can verify a CAPA.'),
        )
        for rec in self:
            if rec.status != 'in_progress':
                raise UserError(self.env._('Only In Progress CAPAs can be verified.'))
            if not rec.effectiveness_conclusion:
                raise UserError(self.env._(
                    'Record the QA conclusion on effectiveness before '
                    'verifying CAPA %s.', rec.name))
            rec._pharma_check_can_verify()
            rec.status = 'verified'
            rec.message_post(body=self.env._('CAPA verified by %s.', self.env.user.name))

    def _pharma_check_can_verify(self):
        """Hook: raise when effectiveness may not be declared yet."""
        self.ensure_one()

    def action_close(self):
        """Close a verified CAPA; restricted to QA Director."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            self.env._('Only QA can close CAPAs.'),
        )
        for rec in self:
            if rec.status != 'verified':
                raise UserError(self.env._(
                    'Only Verified CAPAs can be closed. '
                    'CAPA %(capa)s is currently "%(status)s".',
                    capa=rec.name, status=rec.status))
            if not rec.root_cause:
                raise UserError(self.env._(
                    'Document the Root Cause before closing CAPA %s.', rec.name))
            rec._pharma_check_can_close()
            rec.write({
                'status': 'closed',
                'closed_by': self.env.user.id,
                'closed_on': fields.Datetime.now(),
            })
            rec.message_post(
                body=self.env._('CAPA closed by QA Director %s.', self.env.user.name)
            )
            rec._pharma_after_close()

    def _pharma_check_can_close(self):
        """Hook: raise when this CAPA may not close. A CAPA whose plan is not
        run by the Preventive Action add-on needs its action plan."""
        self.ensure_one()
        if not self.preventive_managed and not self.action_plan:
            raise UserError(self.env._(
                'Document the Action Plan before closing CAPA %s.', self.name))

    def _pharma_after_close(self):
        """Hook: act on a CAPA that has just closed."""
        self.ensure_one()

    def _schedule_summary(self):
        """Render the schedule of a preventive action as one readable line."""
        self.ensure_one()
        nature = dict(self._fields['control_nature'].selection).get(
            self.control_nature, '')
        if self.trigger_type == 'batch':
            return self.env._(
                'on each of the next %(count)s completed test(s) on '
                'material in scope, backstop %(date)s (%(nature)s)',
                count=self.cycle_count,
                date=self.backstop_date or self.env._('set on start'),
                nature=nature,
            )
        if self.trigger_type == 'time':
            uom = dict(self._fields['interval_uom'].selection).get(
                self.interval_uom, '')
            if self.control_nature == 'campaign':
                return self.env._(
                    'every %(count)s %(uom)s, %(cycles)s time(s) (%(nature)s)',
                    count=self.interval_count, uom=uom,
                    cycles=self.cycle_count, nature=nature)
            return self.env._(
                'every %(count)s %(uom)s (%(nature)s)',
                count=self.interval_count, uom=uom, nature=nature)
        return ''

    def write(self, vals):
        """Block reopening a closed CAPA — that is a new deviation, not an edit.

        Where a control established by a CAPA later fails, it is recorded as a
        new deviation linked back to the original. Reopening closed records
        destroys the meaning of the audit trail.
        """
        if 'status' in vals:
            for rec in self:
                if rec.status == 'closed' and vals['status'] != 'closed':
                    raise UserError(self.env._(
                        'CAPA %s is closed and cannot be reopened. Where the '
                        'control it established has failed, raise a new '
                        'deviation linked back to it.', rec.name))
        if 'root_cause' in vals and 'root_cause_overridden' not in vals:
            # An edit counts as an override only when it departs from the
            # deviation; clearing the field follows the deviation again.
            for rec in self:
                deviation = self.env['pharma.deviation'].browse(
                    vals['deviation_id']) if 'deviation_id' in vals \
                    else rec.deviation_id
                text = (vals['root_cause'] or '').strip()
                overridden = bool(text) and \
                    text != (deviation.root_cause or '').strip()
                super(PharmaCapa, rec).write(dict(
                    vals,
                    root_cause=vals['root_cause'] if overridden
                    else deviation.root_cause,
                    root_cause_overridden=overridden,
                ))
            return True
        return super().write(vals)
