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

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

EQUIPMENT_CLASSES = [
    ('testing', 'Testing Instrument'),
    ('manufacturing', 'Manufacturing Equipment'),
    ('utility', 'Utility System'),
]

# Defaults of the site settings, read through _pharma_equipment_settings().
SETTING_DEFAULTS = {
    'check': 'block',
}


STAGE_LABEL_MAP = {'iq': 'IQ', 'oq': 'OQ', 'pq': 'PQ'}


class MaintenanceEquipment(models.Model):
    """GMP register on top of the maintenance equipment.

    Qualification and calibration are tracked separately on purpose: an item
    can be qualified and overdue for calibration, or freshly calibrated and
    never requalified after a move.

    The states below depend on today's date, so the crons recompute them; the
    fitness checks always recompute before reading.
    """
    _inherit = ['maintenance.equipment', 'pharma.workflow.mixin']
    _rec_names_search = ['name', 'equipment_code', 'serial_no']

    # ---- Identification -------------------------------------------------
    equipment_code = fields.Char(
        required=True,
        copy=False,
        tracking=True,
        index=True,
        default='New',
        help='Asset code of the equipment, unique per company. Assigned from '
             'the equipment sequence when left as "New".',
    )
    equipment_class = fields.Selection(
        selection=EQUIPMENT_CLASSES,
        compute='_compute_equipment_class',
        store=True,
        tracking=True,
        help='Class of the equipment category. Testing instruments are '
             'calibrated and can also be cleaned between uses, manufacturing '
             'equipment is cleaned between products, utility systems are '
             'monitored.',
    )
    gmp_critical = fields.Boolean(
        string='GMP Critical',
        tracking=True,
        help='Equipment whose fitness affects product quality. Only GMP '
             'critical manufacturing equipment is checked when a '
             'manufacturing order is confirmed.',
    )

    # ---- Qualification (all classes) ------------------------------------
    qualification_state = fields.Selection(
        selection=[
            ('not_required', 'Not Required'),
            ('in_progress', 'In Progress'),
            ('qualified', 'Qualified'),
            ('requalification_due', 'Requalification Due'),
            ('expired', 'Expired'),
        ],
        string='Qualification',
        compute='_compute_qualification_state',
        store=True,
        tracking=True,
        help='Qualified once IQ, OQ and PQ are done and a qualification date '
             'is set. Due within the requalification warning window; expired '
             'once the requalification date has passed.',
    )
    qualification_date = fields.Date(
        string='Qualified On',
        tracking=True,
        help='Date the qualification (IQ/OQ/PQ) was approved.',
    )
    requalification_date = fields.Date(
        string='Requalification Due',
        tracking=True,
        help='Date by which the equipment must be requalified.',
    )
    requalification_reminder_days = fields.Integer(
        string='Requalification Reminder (Days)',
        default=60,
        tracking=True,
        help='Days before the requalification date that the equipment is due '
             'for requalification, raises a reminder, and is not fit for a batch.',
    )
    qualification_protocol_ref = fields.Char(
        string='Qualification Protocol',
        tracking=True,
        help='Reference of the approved qualification protocol and report.',
    )
    iq_done = fields.Boolean(
        string='IQ Done', tracking=True,
        help='Installation qualification completed.')
    oq_done = fields.Boolean(
        string='OQ Done', tracking=True,
        help='Operational qualification completed.')
    pq_done = fields.Boolean(
        string='PQ Done', tracking=True,
        help='Performance qualification completed.')
    qualification_ids = fields.One2many(
        comodel_name='pharma.equipment.qualification',
        inverse_name='equipment_id',
        string='Qualification Records',
        help='IQ, OQ and PQ records generated when QA approves the protocol.',
    )
    qualification_record_count = fields.Integer(
        string='Record Count', compute='_compute_qualification_record_count')

    @api.depends('qualification_ids')
    def _compute_qualification_record_count(self):
        """Count the IQ, OQ and PQ records, archived ones included."""
        groups = self.env['pharma.equipment.qualification'].with_context(
            active_test=False)._read_group(
            [('equipment_id', 'in', self.ids)], ['equipment_id'], ['__count'])
        counts = {equipment.id: count for equipment, count in groups}
        for equipment in self:
            equipment.qualification_record_count = counts.get(equipment.id, 0)

    # ---- Calibration ----------------------------------------------------
    calibration_required = fields.Boolean(
        tracking=True,
        help='The equipment is calibrated against a traceable standard on a '
             'fixed interval.',
    )
    last_calibration_result_id = fields.Many2one(
        comodel_name='pharma.calibration.result',
        readonly=True,
        tracking=True,
        copy=False,
        help='The last passed calibration, linked by its QA verification. '
             'It holds the date, certificate and check points.',
    )
    last_calibration_date = fields.Date(
        related='last_calibration_result_id.calibration_performed_on',
        string='Last Calibration',
        store=True,
        help='Date of the last passed calibration.',
    )
    calibration_failed_on = fields.Date(
        readonly=True,
        tracking=True,
        copy=False,
        help='Set when a calibration fails; the equipment is out of '
             'calibration until a later calibration passes.',
    )
    next_calibration_date = fields.Date(
        related='last_calibration_result_id.next_calibration_date',
        string='Next Calibration',
        store=True,
        help='Next calibration date of the last passed calibration.',
    )
    calibration_state = fields.Selection(
        selection=[
            ('not_required', 'Not Required'),
            ('ok', 'Calibrated'),
            ('due_soon', 'Due Soon'),
            ('overdue', 'Out of Calibration'),
        ],
        string='Calibration',
        compute='_compute_calibration_state',
        store=True,
        tracking=True,
        help='Out of calibration when never calibrated, past the next '
             'calibration date, or after a failed calibration.',
    )
    calibration_result_ids = fields.One2many(
        comodel_name='pharma.calibration.result',
        inverse_name='equipment_id',
        string='Calibration Records',
    )

    # ---- Cleaning (manufacturing and testing) ---------------------------------------
    cleaning_required = fields.Boolean(
        compute='_compute_cleaning_required',
        store=True,
        readonly=False,
        tracking=True,
        help='The equipment is cleaned after use and before the next batch. '
             'Required by default for testing instruments and manufacturing '
             'equipment; untick it for equipment that is never used in a '
             'process (for example a sealed or single-use item).',
    )
    cleaning_status = fields.Selection(
        selection=[
            ('clean', 'Clean'),
            ('dirty', 'Dirty'),
            ('in_progress', 'Cleaning In Progress'),
        ],
        default='dirty',
        required=True,
        readonly=True,
        copy=False,
        help='Using the equipment makes it dirty; a QA-verified cleaning makes '
             'it clean. Cleaning State also checks the hold times.',
    )
    cleaning_state = fields.Selection(
        selection=[
            ('not_required', 'Not Required'),
            ('clean', 'Clean'),
            ('dirty', 'Dirty'),
            ('in_progress', 'Cleaning In Progress'),
            ('hold_expired', 'Clean Hold Expired'),
            ('dirty_hold_expired', 'Dirty Hold Expired'),
        ],
        compute='_compute_cleaning_state',
        store=True,
        tracking=True,
        help='Clean Hold Expired: cleaned, but left unused too long, so clean '
             'it again before use. Dirty Hold Expired: used, but left dirty too '
             'long before cleaning, so QA will check the cleaning.',
    )
    last_cleaning_request_id = fields.Many2one(
        comodel_name='maintenance.request',
        string='Last Cleaning Record',
        readonly=True,
        tracking=True,
        copy=False,
        help='The most recent QA-verified cleaning request. It holds who '
             'cleaned the equipment and when.',
    )
    last_cleaned_on = fields.Datetime(
        related='last_cleaning_request_id.completed_on', string='Last Cleaned On',
        store=True, help='When the last QA-verified cleaning was completed.')
    clean_valid_until = fields.Datetime(
        string='Clean Until',
        compute='_compute_clean_valid_until',
        store=True,
        help='The equipment stays clean until this time if it is not used.',
    )
    dirty_hold_until = fields.Datetime(
        string='Clean Before',
        compute='_compute_dirty_hold_until',
        store=True,
        help='The equipment is dirty: start cleaning it before this time.',
    )
    cleaning_request_ids = fields.One2many(
        comodel_name='maintenance.request',
        inverse_name='equipment_id',
        string='Cleaning Records',
        domain=[('maintenance_type', '=', 'cleaning')],
    )
    last_product_id = fields.Many2one(
        comodel_name='product.product',
        readonly=True,
        tracking=True,
        copy=False,
        help='Product of the last batch made on the equipment. A different '
             'product next is a changeover.',
    )
    last_used_on = fields.Datetime(
        readonly=True, copy=False,
        help='When the last batch made on the equipment was completed.')
    product_dedicated = fields.Boolean(
        string='Dedicated to One Product',
        tracking=True,
        help='The equipment may only make the product that last ran on it.',
    )

    # ---- Sterile (optional, site-wide switch) ---------------------------
    sterilisation_required = fields.Boolean(
        compute='_compute_sterilisation_required',
        store=True,
        tracking=True,
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='Manufacturing equipment of a sterile category: it is sterilised '
             'after cleaning before it is used for a sterile product.',
    )
    last_sterilisation_request_id = fields.Many2one(
        comodel_name='maintenance.request',
        string='Last Sterilisation Record',
        readonly=True,
        copy=False,
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='The most recent QA-verified cleaning whose sterilisation cycle passed.',
    )
    last_sterilised_on = fields.Datetime(
        related='last_sterilisation_request_id.completed_on',
        string='Last Sterilised On',
        store=True,
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='When the last QA-verified sterilisation cycle passed.',
    )
    sterile_valid_until = fields.Datetime(
        string='Sterile Until',
        compute='_compute_sterile_valid_until',
        store=True,
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='Last sterilisation plus its sterile-hold time.',
    )
    sterilisation_request_ids = fields.One2many(
        comodel_name='maintenance.request',
        inverse_name='equipment_id',
        string='Sterilisation Records',
        domain=[('maintenance_type', '=', 'cleaning'), ('sterilisation_performed', '=', True)],
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
    )
    sterile_state = fields.Selection(
        selection=[
            ('not_required', 'Not Required'),
            ('sterile', 'Sterile'),
            ('not_sterile', 'Not Sterile'),
            ('hold_expired', 'Sterile Hold Expired'),
        ],
        compute='_compute_sterile_state',
        store=True,
        groups='pharma_equipment_maintenance.group_pharma_sterile_mfg',
        help='Not sterile until a passed cycle, and again once the equipment '
             'is used after it.',
    )

    # ---- Relations ------------------------------------------------------
    workcenter_ids = fields.Many2many(
        comodel_name='mrp.workcenter',
        relation='pharma_equipment_workcenter_rel',
        column1='equipment_id',
        column2='workcenter_id',
        string='Work Centres',
        help='Work centres this equipment is used at. Manufacturing orders '
             'routed through them check its fitness on confirmation.',
    )
    value_source_ids = fields.One2many(
        comodel_name='pharma.value.source',
        inverse_name='equipment_id',
        string='Measurement Sources',
        help='Registered devices (balances, sensors) belonging to this equipment.',
    )
    open_breakdown = fields.Boolean(
        string='Under Breakdown Repair',
        compute='_compute_open_breakdown',
        search='_search_open_breakdown',
        help='A corrective request is open and not yet QA verified.',
    )
    impacted_result_count = fields.Integer(
        string='Results Since Last Calibration',
        compute='_compute_impacted_result_count',
        help='QC results measured with this instrument since its last passed '
             'calibration.',
    )

    _equipment_code_company_uniq = models.Constraint(
        'unique(equipment_code, company_id)',
        'The equipment code must be unique per company.',
    )

    def _auto_init(self):
        """Number existing equipment before the code becomes required and unique.

        Every row would otherwise get the default "New" and the unique
        constraint could not be added. The post-init hook moves the sequence
        past the codes given here.
        """
        cr = self.env.cr
        cr.execute("ALTER TABLE maintenance_equipment ADD COLUMN IF NOT EXISTS equipment_code VARCHAR")
        cr.execute("""
            UPDATE maintenance_equipment e
               SET equipment_code = 'EQ-' || lpad(n.rn::text, 4, '0')
              FROM (SELECT id, row_number() OVER (ORDER BY id) AS rn
                      FROM maintenance_equipment
                     WHERE equipment_code IS NULL) n
             WHERE e.id = n.id
        """)
        return super()._auto_init()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    @api.model
    def _pharma_equipment_settings(self):
        """The site settings of the equipment checks, with their defaults."""
        params = self.env['ir.config_parameter'].sudo()
        check = params.get_param('pharma_equipment.check') or SETTING_DEFAULTS['check']
        if check not in ('off', 'warn', 'block'):
            check = SETTING_DEFAULTS['check']

        return {'check': check}

    @api.model
    def _pharma_sterile_enabled(self):
        """Whether sterile manufacturing is switched on for the site."""
        group = self.env.ref(
            'pharma_equipment_maintenance.group_pharma_sterile_mfg',
            raise_if_not_found=False)
        return bool(group) and group in self.env.ref('base.group_user').sudo().implied_ids

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('category_id.equipment_class')
    def _compute_equipment_class(self):
        """The category decides the class."""
        for equipment in self:
            equipment.equipment_class = equipment.category_id.equipment_class

    @api.depends('category_id.pharma_sterile', 'category_id.equipment_class')
    def _compute_sterilisation_required(self):
        """Manufacturing equipment of a sterile category is sterilised."""
        for equipment in self.sudo():
            category = equipment.category_id
            equipment.sterilisation_required = (
                category.pharma_sterile and category.equipment_class == 'manufacturing')

    @api.depends('gmp_critical', 'iq_done', 'oq_done', 'pq_done',
                 'qualification_date', 'requalification_date',
                 'requalification_reminder_days', 'qualification_protocol_ref')
    def _compute_qualification_state(self):
        """Derive the qualification state from IQ/OQ/PQ and the dates."""
        today = fields.Date.context_today(self)
        for equipment in self:
            qualified = (equipment.iq_done and equipment.oq_done
                         and equipment.pq_done and equipment.qualification_date)
            started = (equipment.iq_done or equipment.oq_done or equipment.pq_done
                       or equipment.qualification_protocol_ref)
            requal = equipment.requalification_date
            warn = timedelta(days=equipment.requalification_reminder_days)
            if not qualified:
                state = 'in_progress' if (equipment.gmp_critical or started) else 'not_required'
            elif requal and requal < today:
                state = 'expired'
            elif requal and requal <= today + warn:
                state = 'requalification_due'
            else:
                state = 'qualified'
            equipment.qualification_state = state

    @api.depends('calibration_required', 'next_calibration_date',
                 'calibration_failed_on', 'last_calibration_date',
                 'last_calibration_result_id.calibration_reminder_days')
    def _compute_calibration_state(self):
        """Calibrated, due soon, or out of calibration."""
        today = fields.Date.context_today(self)
        for equipment in self:
            nxt = equipment.next_calibration_date
            warn = timedelta(days=equipment.last_calibration_result_id.calibration_reminder_days)
            if not equipment.calibration_required:
                state = 'not_required'
            elif equipment.calibration_failed_on or not nxt or nxt < today:
                state = 'overdue'
            elif nxt <= today + warn:
                state = 'due_soon'
            else:
                state = 'ok'
            equipment.calibration_state = state

    @api.depends('last_cleaned_on', 'last_cleaning_request_id.clean_hold_hours')
    def _compute_clean_valid_until(self):
        """Last cleaning plus its clean-hold time."""
        for equipment in self:
            hours = equipment.last_cleaning_request_id.clean_hold_hours
            if equipment.last_cleaned_on and hours > 0:
                equipment.clean_valid_until = equipment.last_cleaned_on + timedelta(hours=hours)
            else:
                equipment.clean_valid_until = False

    @api.depends('category_id.equipment_class')
    def _compute_cleaning_required(self):
        """Testing instruments and manufacturing equipment are cleaned."""
        for equipment in self:
            equipment_class = equipment.category_id.equipment_class
            if equipment_class:
                equipment.cleaning_required = equipment_class in ('testing', 'manufacturing')
            else:
                equipment.cleaning_required = equipment.cleaning_required

    @api.depends('last_used_on', 'last_cleaning_request_id.dirty_hold_hours',
                 'cleaning_required', 'cleaning_status')
    def _compute_dirty_hold_until(self):
        """Last use plus the dirty-hold time, while the equipment is dirty."""
        for equipment in self:
            hours = equipment.last_cleaning_request_id.dirty_hold_hours
            if (equipment.cleaning_required and equipment.cleaning_status == 'dirty'
                    and equipment.last_used_on and hours > 0):
                equipment.dirty_hold_until = equipment.last_used_on + timedelta(hours=hours)
            else:
                equipment.dirty_hold_until = False

    @api.depends('cleaning_required', 'cleaning_status', 'clean_valid_until', 'dirty_hold_until')
    def _compute_cleaning_state(self):
        """Apply the clean-hold and dirty-hold expiry on top of the physical
        cleaning status."""
        now = fields.Datetime.now()
        for equipment in self:
            if not equipment.cleaning_required:
                state = 'not_required'
            elif (equipment.cleaning_status == 'clean' and equipment.clean_valid_until
                    and equipment.clean_valid_until < now):
                state = 'hold_expired'
            elif (equipment.cleaning_status == 'dirty' and equipment.dirty_hold_until
                    and equipment.dirty_hold_until < now):
                state = 'dirty_hold_expired'
            else:
                state = equipment.cleaning_status
            equipment.cleaning_state = state

    @api.depends('last_sterilised_on', 'last_sterilisation_request_id.sterile_hold_hours')
    def _compute_sterile_valid_until(self):
        """Last sterilisation plus its sterile-hold time."""
        for equipment in self.sudo():
            hours = equipment.last_sterilisation_request_id.sterile_hold_hours
            if equipment.last_sterilised_on and hours > 0:
                equipment.sterile_valid_until = (
                    equipment.last_sterilised_on + timedelta(hours=hours))
            else:
                equipment.sterile_valid_until = False

    @api.depends('sterilisation_required', 'last_sterilised_on',
                 'sterile_valid_until', 'last_used_on', 'cleaning_status')
    def _compute_sterile_state(self):
        """Sterile after a passed cycle, until it is used or the hold runs out."""
        now = fields.Datetime.now()
        for equipment in self:
            sterilised = equipment.last_sterilised_on
            if not equipment.sterilisation_required:
                state = 'not_required'
            elif (not sterilised or equipment.cleaning_status != 'clean'
                    or (equipment.last_used_on and equipment.last_used_on >= sterilised)):
                state = 'not_sterile'
            elif equipment.sterile_valid_until and equipment.sterile_valid_until < now:
                state = 'hold_expired'
            else:
                state = 'sterile'
            equipment.sterile_state = state

    @api.depends('maintenance_ids.maintenance_type', 'maintenance_ids.pharma_state',
                 'maintenance_ids.archive')
    def _compute_open_breakdown(self):
        """Whether a corrective request is open on the equipment."""
        open_ids = set(self.env['maintenance.request'].sudo().search(
            self._open_breakdown_domain() + [('equipment_id', 'in', self.ids)]
        ).equipment_id.ids) if self.ids else set()
        for equipment in self:
            equipment.open_breakdown = equipment.id in open_ids

    @api.model
    def _open_breakdown_domain(self):
        """Corrective requests not yet released back to use by QA."""
        return [
            ('maintenance_type', '=', 'corrective'),
            ('pharma_state', '!=', 'qa_verified'),
            ('archive', '=', False),
        ]

    def _search_open_breakdown(self, operator, value):
        """Search equipment with (or without) an open corrective request."""
        if operator not in ('=', '!='):
            return NotImplemented
        requests = self.env['maintenance.request'].search(self._open_breakdown_domain())
        positive = (operator == '=') == bool(value)
        return [('id', 'in' if positive else 'not in', requests.equipment_id.ids)]

    def _compute_impacted_result_count(self):
        """Count the results measured since the last passed calibration."""
        ResultLine = self.env['pharma.qc.result.line']
        for equipment in self:
            equipment.impacted_result_count = ResultLine.search_count(
                equipment._impacted_result_domain()) if equipment.id else 0

    # ------------------------------------------------------------------
    # Onchange / CRUD
    # ------------------------------------------------------------------
    @api.onchange('category_id')
    def _onchange_category_id_pharma(self):
        """Take the GMP flag of the category for a new equipment, and propose
        the obligations that come with its class."""
        category = self.category_id
        if not category:
            return
        if not self._origin.id:
            self.gmp_critical = category.gmp_critical
        if category.equipment_class == 'testing':
            self.calibration_required = True

    @api.model_create_multi
    def create(self, vals_list):
        """Number new equipment and take the category GMP flag."""
        Category = self.env['maintenance.equipment.category']
        for vals in vals_list:
            if vals.get('category_id'):
                vals.setdefault('gmp_critical', Category.browse(vals['category_id']).gmp_critical)
            if not vals.get('equipment_code') or vals['equipment_code'] == 'New':
                vals['equipment_code'] = self._pharma_next_code(
                    vals.get('company_id') or self.env.company.id)
        equipment = super().create(vals_list)
        equipment._pharma_generate_qualification_records()
        return equipment

    def write(self, vals):
        """Registering equipment as GMP critical generates its qualification records."""
        result = super().write(vals)
        if vals.get('gmp_critical'):
            self._pharma_generate_qualification_records()
        return result

    @api.model
    def _pharma_next_code(self, company_id):
        """Next sequence code not already taken in the company.

        Codes entered by hand, or given to existing equipment on install,
        may already use numbers the sequence has not reached.
        """
        Sequence = self.env['ir.sequence']
        for _attempt in range(1000):
            code = Sequence.next_by_code('pharma.equipment')
            if not code:
                return 'New'
            if not self.with_context(active_test=False).search_count([
                    ('equipment_code', '=', code), ('company_id', '=', company_id)]):
                return code
        return code

    @api.constrains('gmp_critical', 'category_id')
    def _check_gmp_category(self):
        """GMP critical equipment needs a classified category: the class
        decides which fitness rules apply to it."""
        for equipment in self:
            if equipment.gmp_critical and not equipment.category_id.equipment_class:
                raise ValidationError(self.env._(
                    'GMP critical equipment "%s" needs a category with an '
                    'equipment class.', equipment.display_name))

    @api.constrains('qualification_date', 'requalification_date')
    def _check_qualification_dates(self):
        """Requalification cannot fall before the qualification."""
        for equipment in self:
            if (equipment.qualification_date and equipment.requalification_date
                    and equipment.requalification_date < equipment.qualification_date):
                raise ValidationError(self.env._(
                    'The requalification date of "%s" cannot be earlier than '
                    'its qualification date.', equipment.display_name))

    @api.depends('equipment_code')
    def _compute_display_name(self):
        """Lead with the equipment code, as on the shop floor."""
        res = super()._compute_display_name()
        for equipment in self:
            if equipment.equipment_code and equipment.equipment_code != 'New':
                equipment.display_name = '[%s] %s' % (
                    equipment.equipment_code, equipment.display_name)
        return res

    # ------------------------------------------------------------------
    # Fitness
    # ------------------------------------------------------------------
    def _pharma_refresh_states(self):
        """Recompute the date-dependent states so a check never reads a stale one."""
        if not self:
            return
        names = ['qualification_state', 'calibration_state', 'cleaning_state']
        if self._pharma_sterile_enabled():
            names.append('sterile_state')
        records = self.sudo()
        for name in names:
            self.env.add_to_compute(records._fields[name], records)
        records.flush_recordset(names)

    def _pharma_fitness_issues(self, product=False, sterile=False):
        """Reasons the equipment is unfit for a batch of ``product``.

        :param product: product.product to be made, for changeover checks
        :param sterile: whether the batch is a sterile product
        :return: list of human-readable reasons, empty when fit
        """
        self.ensure_one()
        equipment = self.sudo()
        issues = []
        if equipment.calibration_state == 'overdue':
            issues.append(self.env._('out of calibration'))
        if equipment.qualification_state == 'requalification_due':
            issues.append(self.env._('requalification due on %s', equipment.requalification_date))
        elif equipment.qualification_state == 'expired':
            issues.append(self.env._('qualification expired on %s', equipment.requalification_date))
        if equipment.open_breakdown:
            issues.append(self.env._('under breakdown repair'))
        if equipment.cleaning_state in ('dirty', 'in_progress', 'dirty_hold_expired'):
            if equipment.last_product_id and product and equipment.last_product_id != product:
                issues.append(self.env._('not cleaned since %s ran on it', equipment.last_product_id.display_name))
            else:
                issues.append(self.env._('not clean'))
        elif equipment.cleaning_state == 'hold_expired':
            issues.append(self.env._('clean hold expired on %s', fields.Datetime.context_timestamp(
                self, equipment.clean_valid_until).strftime('%Y-%m-%d %H:%M')))
        if (equipment.product_dedicated and product and equipment.last_product_id
                and equipment.last_product_id != product):
            issues.append(self.env._('dedicated to %s', equipment.last_product_id.display_name))
        if sterile and self._pharma_sterile_enabled():
            if equipment.sterile_state == 'not_sterile':
                issues.append(self.env._('not sterile'))
            elif equipment.sterile_state == 'hold_expired':
                issues.append(self.env._('sterile hold expired'))
        return issues

    def _pharma_register_use(self, product, when=None):
        """Record that a batch of ``product`` was made: the equipment is dirty."""
        vals = {
            'last_product_id': product.id,
            'last_used_on': when or fields.Datetime.now(),
        }
        self.sudo().filtered('cleaning_required').write(dict(vals, cleaning_status='dirty'))
        self.sudo().filtered(lambda e: not e.cleaning_required).write(vals)

    # ------------------------------------------------------------------
    # Calibration impact
    # ------------------------------------------------------------------
    def _impacted_result_domain(self):
        """Results measured with this instrument since its last passed calibration."""
        self.ensure_one()
        return self._impacted_result_domain_for(self.last_calibration_date)

    def _impacted_result_domain_for(self, calibration_date):
        """Results measured under the calibration of the given date (all, when it was never calibrated)."""
        self.ensure_one()
        domain = [
            '|', ('instrument_id', '=', self.id), ('support_instrument_ids', 'in', self.id),
            ('result_entered', '=', True),
        ]
        if calibration_date:
            domain.append(('instrument_calibration_date', '=', calibration_date))
        return domain

    def _pharma_impact_action(self, domain, name):
        """Window action listing the QC results of an impact assessment."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'pharma.qc.result.line',
            'view_mode': 'list,form',
            'views': [(self.env.ref(
                'pharma_equipment_maintenance.pharma_qc_result_line_view_list_impact').id, 'list'),
                (False, 'form')],
            'domain': domain,
            'context': {'group_by': ['test_order_id'], 'create': False},
        }

    def action_calibration_impact_assessment(self):
        """Every result this instrument produced since it last passed calibration."""
        self.ensure_one()
        return self._pharma_impact_action(
            self._impacted_result_domain(), self.env._('Calibration Impact: %s', self.display_name))

    def action_view_impacted_batches(self):
        """The batches whose release rests on results from this instrument."""
        self.ensure_one()
        results = self.env['pharma.qc.result.line'].search(self._impacted_result_domain())
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Batches Tested With %s', self.display_name),
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('id', 'in', results.test_order_id.lot_id.ids)],
            'context': {'create': False},
        }

    def action_view_calibrations(self):
        """Calibration records of the equipment."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Calibrations'),
            'res_model': 'pharma.calibration.result',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'default_equipment_id': self.id},
        }

    def action_view_cleanings(self):
        """Cleaning history of the equipment."""
        self.ensure_one()
        return self._pharma_request_action('cleaning', self.env._('Cleaning Log'))

    def _pharma_request_action(self, maintenance_type, name):
        """Requests of one type for this equipment, ready to raise a new one."""
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'maintenance.request',
            'view_mode': 'list,kanban,form',
            'domain': [('equipment_id', '=', self.id), ('maintenance_type', '=', maintenance_type)],
            'context': self._pharma_request_context(maintenance_type, name),
        }

    def _pharma_request_context(self, maintenance_type, name):
        """Defaults of a new request of ``maintenance_type`` on this equipment.
        A cleaning of sterile equipment is sterilised after cleaning by default."""
        self.ensure_one()
        context = {
            'default_equipment_id': self.id,
            'default_maintenance_type': maintenance_type,
            'default_name': '%s: %s' % (name, self.name),
            'default_company_id': self.company_id.id or self.env.company.id,
        }
        if (maintenance_type == 'cleaning' and self._pharma_sterile_enabled()
                and self.sudo().sterilisation_required):
            context['default_sterilisation_performed'] = True
        return context

    def _pharma_generate_qualification_records(self):
        """Create the IQ, OQ and PQ records of GMP critical equipment.

        Like SOP training records they are generated by the system, so
        they are created elevated; stages already ticked on the register
        are recorded as passed.
        """
        Qualification = self.env['pharma.equipment.qualification'].sudo().with_context(
            active_test=False)
        for equipment in self.sudo().filtered('gmp_critical'):
            if Qualification.search_count([('equipment_id', '=', equipment.id)]):
                continue
            for stage in ('iq', 'oq', 'pq'):
                vals = {'equipment_id': equipment.id, 'stage': stage}
                if equipment[stage + '_done']:
                    vals.update({
                        'state': 'passed',
                        'performed_on': equipment.qualification_date,
                        'report_ref': equipment.qualification_protocol_ref or self.env._('Register'),
                        'notes': self.env._('Carried over from the equipment register.'),
                        'signed_by': self.env.user.id,
                        'signed_on': fields.Datetime.now(),
                    })
                Qualification.create(vals)

    def _pharma_sync_qualification(self, record):
        """Write a signed IQ/OQ/PQ outcome to the equipment flags and dates."""
        self.ensure_one()
        passed = record.state == 'passed'
        vals = {record.stage + '_done': passed}
        stages = self.qualification_ids
        if passed and all(r.state == 'passed' for r in stages) and len(stages) == 3:
            done_on = max(stages.mapped('performed_on'))
            vals['qualification_date'] = done_on
            if not self.requalification_date or self.requalification_date <= done_on:
                vals['requalification_date'] = done_on + relativedelta(years=1)
        elif not passed:
            vals['qualification_date'] = False
        self.write(vals)
        self.message_post(body=self.env._(
            '%(stage)s %(result)s on %(date)s, signed off by %(user)s.',
            stage=STAGE_LABEL_MAP[record.stage],
            result=self.env._('passed') if passed else self.env._('failed'),
            date=record.performed_on, user=self.env.user.name))

    def action_view_qualifications(self):
        """IQ, OQ and PQ records of the equipment."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Qualification Records'),
            'res_model': 'pharma.equipment.qualification',
            'view_mode': 'list,form',
            'domain': [('equipment_id', '=', self.id)],
            'context': {'active_test': False, 'default_equipment_id': self.id},
        }

    def action_raise_calibration(self):
        """Open a new calibration of this equipment."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Calibration'),
            'res_model': 'pharma.calibration.result',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_equipment_id': self.id},
        }

    def action_raise_cleaning(self):
        """Open a new cleaning request for this equipment."""
        return self._pharma_new_request('cleaning', self.env._('Cleaning'))

    def action_raise_breakdown(self):
        """Open a new breakdown (corrective) request for this equipment."""
        return self._pharma_new_request('corrective', self.env._('Breakdown'))

    def _pharma_new_request(self, maintenance_type, label):
        """Form of a new request of ``maintenance_type`` on this equipment."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': label,
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'target': 'current',
            'context': self._pharma_request_context(maintenance_type, label),
        }

    # ------------------------------------------------------------------
    # Crons
    # ------------------------------------------------------------------
    def _pharma_remind(self, activity_xmlid, summary, deadline):
        """Schedule a reminder activity once per open reminder."""
        activity_type = self.env.ref(activity_xmlid)
        for equipment in self:
            if equipment.activity_ids.filtered(
                    lambda a, t=activity_type: a.activity_type_id == t):
                continue
            user = equipment.technician_user_id or equipment.owner_user_id \
                or equipment.maintenance_team_id.member_ids[:1] or self.env.ref('base.user_admin')
            equipment.activity_schedule(
                activity_xmlid,
                date_deadline=deadline(equipment) or fields.Date.context_today(self),
                summary=summary,
                user_id=user.id,
            )

    @api.model
    def _cron_pharma_calibration_due(self):
        """Refresh calibration states; remind ahead of the due date."""
        equipment = self.search([('calibration_required', '=', True)])
        before = {e.id: e.calibration_state for e in equipment}
        equipment._pharma_refresh_states()
        due = equipment.filtered(lambda e: e.calibration_state in ('due_soon', 'overdue'))
        due._pharma_remind(
            'pharma_equipment_maintenance.mail_activity_calibration_due',
            self.env._('Calibration due'), lambda e: e.next_calibration_date)
        for item in equipment.filtered(
                lambda e: e.calibration_state == 'overdue' and before[e.id] != 'overdue'):
            item.message_post(body=self.env._('Calibration is overdue: the equipment is now '
                                              'out of calibration.'))

    @api.model
    def _cron_pharma_qualification_due(self):
        """Refresh qualification states; remind ahead of requalification."""
        equipment = self.search([('qualification_state', '!=', 'not_required')])
        before = {e.id: e.qualification_state for e in equipment}
        equipment._pharma_refresh_states()
        due = equipment.filtered(
            lambda e: e.qualification_state in ('requalification_due', 'expired'))
        due._pharma_remind(
            'pharma_equipment_maintenance.mail_activity_requalification_due',
            self.env._('Requalification due'), lambda e: e.requalification_date)
        for item in equipment.filtered(
                lambda e: e.qualification_state == 'expired' and before[e.id] != 'expired'):
            item.message_post(body=self.env._('Qualification has expired.'))

    @api.model
    def _cron_pharma_hold_expiry(self):
        """Expire clean, dirty and sterile holds that have run out."""
        now = fields.Datetime.now()
        clean = self.search([('cleaning_state', '=', 'clean'),
                             ('clean_valid_until', '!=', False),
                             ('clean_valid_until', '<', now)])
        clean._pharma_refresh_states()
        for item in clean:
            item.message_post(body=self.env._('Clean hold expired: clean the equipment again before use.'))
        dirty = self.search([('cleaning_state', '=', 'dirty'),
                             ('dirty_hold_until', '!=', False),
                             ('dirty_hold_until', '<', now)])
        dirty._pharma_refresh_states()
        for item in dirty:
            item.message_post(body=self.env._(
                'Dirty hold expired: the equipment was not cleaned in time after '
                'use. Its next cleaning will be flagged for QA.'))
        if self._pharma_sterile_enabled():
            sterile = self.sudo().search([('sterile_state', '=', 'sterile'),
                                          ('sterile_valid_until', '!=', False),
                                          ('sterile_valid_until', '<', now)])
            sterile._pharma_refresh_states()
            for item in sterile:
                item.message_post(body=self.env._(
                    'Sterile hold expired: sterilise the equipment again before '
                    'a sterile batch.'))
