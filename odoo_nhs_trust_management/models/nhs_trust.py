# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class NhsTrust(models.Model):
    _name = 'nhs.trust'
    _description = 'NHS Trust'
    _order = 'name'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Trust Name',
        required=True,
        tracking=True,
        index=True,
        help="Trust legal name as registered with Companies House /"
             " Scottish Govt (e.g. 'Barts Health NHS Trust'). Indexed for search."
    )
    short_name = fields.Char(
        string='Short Name',
        tracking=True,
        help="Display name used on cards, breadcrumbs, and PDF headers (e.g. 'Barts Health')."
             " Falls back to name if blank."
    )
    ods_code = fields.Char(
        string='ODS Code',
        required=True,
        tracking=True,
        index=True,
        help="Organisation Data Service code from NHS Digital."
             " The single canonical identifier for an NHS organisation across all NHS data flows. "
             "Examples: 'RJ1', 'RGT', 'S08000021'. 2–10 chars, uppercase."
             " Unique across the database (SQL constraint). Indexed."
    )
    health_system = fields.Selection([
        ('nhs_england', 'NHS England'),
        ('nhs_scotland', 'NHS Scotland'),
    ],
        string='NHS Health System',
        required=True,
        default='nhs_england',
        tracking=True,
        index=True,
        help="Selection: 'nhs_england' or 'nhs_scotland'. Default: 'nhs_england'."
             " Drives field visibility on the form: NHS England fields (ICB, ICS) hide for Scotland; "
             "Health Board field hides for England. Changing this clears mutually exclusive references."
    )
    trust_type_id = fields.Many2one(
        'nhs.trust.type',
        string='Trust Type',
        required=True,
        tracking=True,
        index=True,
        domain="[('health_system', 'in', (health_system, 'both'))]",
        help="Classification. Dropdown is filtered by health_system."
    )
    foundation_trust = fields.Boolean(
        string='Foundation Trust',
        default=False,
        tracking=True,
        help="Tick if authorised as an NHS Foundation Trust by NHS England (formerly Monitor)."
             " Foundation Trusts have additional autonomy and a Council of Governors."

    )
    foundation_authorised_date = fields.Date(
        string='Foundation Authorisation Date',
        tracking=True,
        help="The date NHSE authorised foundation status. Required when foundation_trust=True."
    )

    # Governance & Legal details
    companies_house_number = fields.Char(
        string='Companies House Number',
        tracking=True,
        help="Companies House registration number. Only Foundation Trusts have one — shown only"
             " when foundation_trust=True."
    )
    vat_number = fields.Char(
        string='VAT Registration Number',
        tracking=True,
        help="VAT registration number. NHS bodies are generally outside the"
             " scope of VAT but some have it for trading activities."
    )
    establishment_date = fields.Date(
        string='Establishment Date',
        tracking=True,
        help="Date the Trust was established as a legal entity."
    )

    # Relationships & Geography
    region_id = fields.Many2one(
        'nhs.region',
        string='NHS Region',
        required=True,
        index=True,
        tracking=True,
        domain="[('health_system', '=', health_system)]",
        help="Region — filtered to those matching the chosen health_system. Required for all trusts."
    )
    icb_id = fields.Many2one(
        'nhs.icb',
        string='Integrated Care Board (ICB)',
        index=True,
        tracking=True,
        help="Integrated Care Board. Required when health_system='nhs_england'."
             " Domain restricts to ICBs in the selected region. Drives record-level"
             " security — NHS Trust Users only see trusts within their allowed ICBs."
    )
    ics_id = fields.Many2one(
        'nhs.ics',
        string='Integrated Care System (ICS)',
        index=True,
        tracking=True,
        help="Optional ICS sub-grouping. Domain restricts to ICSs of the selected ICB. England only."
    )
    health_board_id = fields.Many2one(
        'nhs.health.board',
        string='NHS Health Board',
        index=True,
        tracking=True,
        help="Required when health_system='nhs_scotland'. Hidden for England. Drives record-level"
             " security for Scottish users via res.users.nhs_allowed_health_board_ids."
    )
    company_id = fields.Many2one(
        'res.company',
        string='Odoo Company Reference',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        help="Optional link to an Odoo res.company. Hybrid model: leave blank for trusts that share the default company,"
             " or set to a dedicated company for separated accounting and multi-company users."
             " Important: this is NOT the same as Odoo's multi-company restrictions — those"
             " are deferred to the future phase that integrates Accounting."
    )

    # Address & Contact info
    street = fields.Char(
        string='Street',
        help="Standard address fields for the Trust's main / registered HQ."
             " Not synced to a res.partner because the Trust is not a contact."
    )
    street2 = fields.Char(
        string='Street 2',
        help="Standard address fields for the Trust's main / registered HQ. "
             "Not synced to a res.partner because the Trust is not a contact."
    )
    city = fields.Char(
        string='City',
        help="Standard address fields for the Trust's main / registered HQ."
             " Not synced to a res.partner because the Trust is not a contact."
    )
    county = fields.Char(
        string='County',
        help="Standard address fields for the Trust's main / registered HQ."
             " Not synced to a res.partner because the Trust is not a contact."
    )
    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        ondelete='restrict',
        domain="[('country_id', '=?', country_id)]",
        help="Standard Odoo state/county field for the Trust's main / registered HQ."
    )
    zip = fields.Char(
        string='Postcode',
        help="Standard address fields for the Trust's main / registered HQ."
             " Not synced to a res.partner because the Trust is not a contact."
    )
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        default=lambda self: self.env.ref('base.uk', raise_if_not_found=False),
        required=True,
        help="Defaults to United Kingdom."
    )
    phone = fields.Char(
        string='Phone',
        help="Main switchboard / general enquiries contact details. Rendered with the standard phone widget."
    )
    email = fields.Char(
        string='Email',
        help="Main switchboard / general enquiries contact details. Rendered with the standard email widget."
    )
    website = fields.Char(
        string='Website',
        help="Main switchboard / general enquiries contact details. Rendered with the standard url widget."
    )

    # Governance Leadership (Many2one -> res.partner)
    chair_id = fields.Many2one(
        'res.partner',
        string='Board Chair',
        tracking=True,
        index=True,
        help="Chair of the board. Stored as a contact so they can also appear in the board_member_ids list."
    )
    chief_executive_id = fields.Many2one(
        'res.partner',
        string='Chief Executive',
        tracking=True,
        index=True,
        help="CEO / Accountable Officer. Tracked on chatter — changes are logged automatically."
    )
    medical_director_id = fields.Many2one(
        'res.partner',
        string='Medical Director',
        tracking=True,
        index=True,
        help="Medical Director — clinical leadership and Caldicott Guardian role often sits here."
    )
    director_of_nursing_id = fields.Many2one(
        'res.partner',
        string='Director of Nursing',
        tracking=True,
        index=True,
        help="Chief Nurse / Director of Nursing."
    )
    finance_director_id = fields.Many2one(
        'res.partner',
        string='Director of Finance',
        tracking=True,
        index=True,
        help="Director of Finance."
    )

    # Board Members List & State
    board_member_ids = fields.One2many(
        'res.partner',
        'nhs_trust_id',
        string='Board Members',
        domain=[('is_nhs_board_member', '=', True)],
        help="All board members. Filtered domain ('is_nhs_board_member','=',True). "
             "When adding from this o2m, context defaults set is_nhs_board_member=True"
             " and is_company=False automatically."
    )
    board_member_count = fields.Integer(
        string='Board Member Count',
        compute='_compute_board_member_count',
        help="Count of board members. Shown on the stat button."
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('active', 'Active'),
        ('special_measures', 'Special Measures'),
        ('suspended', 'Suspended'),
        ('merging', 'Merging'),
        ('dissolved', 'Dissolved'),
    ],
        string='Workflow State',
        required=True,
        default='draft',
        tracking=True,
        index=True,
        copy=False,
        group_expand=True,
        help="Selection: draft / under_review / active / special_measures / suspended / merging / dissolved. "
             "Default: 'draft'. DO NOT write to this field directly — write() is overridden"
             " to raise UserError unless approved_state_change context is set. Use State Change Wizard."
    )

    state_log_ids = fields.One2many(
        'nhs.trust.state.log',
        'trust_id',
        string='State Audit History',
        help="Immutable audit log of every state transition. Read-only — even managers cannot edit existing entries."
    )
    description = fields.Html(
        string='Description / Clinical Notes',
        help="Rich-text description / notes. Free-form internal field."
    )
    color = fields.Integer(
        string='Color Index',
        default=0,
        help="Kanban color index (0–11). Used by users to colour-code cards manually."
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Archive flag."
    )

    _ods_code_unique = models.Constraint(
        'unique(ods_code)',
        'The ODS code must be unique!',
    )

    @api.constrains('ods_code', 'health_system')
    def _check_ods_code(self):
        for trust in self:
            if not trust.ods_code:
                continue
            code = trust.ods_code
            if not code.isalnum():
                raise ValidationError('The ODS code must contain alphanumeric characters only!')

            if trust.health_system == 'nhs_england':
                if not (3 <= len(code) <= 5):
                    raise ValidationError('NHS England ODS codes must be between 3 and 5 characters long!')
            elif trust.health_system == 'nhs_scotland':
                if not code.startswith('S'):
                    raise ValidationError("NHS Scotland ODS codes must start with 'S'!")
                if not (3 <= len(code) <= 10):
                    raise ValidationError('NHS Scotland ODS codes must be between 3 and 10 characters long!')

    @api.constrains('health_system', 'icb_id', 'health_board_id', 'region_id')
    def _check_geographic_fields(self):
        if self.env.context.get('nhs_ods_sync'):
            return
        for trust in self:
            if trust.region_id and trust.region_id.health_system != trust.health_system:
                raise ValidationError('The selected NHS Region must match the NHS Health System of this Trust!')

            if trust.health_system == 'nhs_england':
                if not trust.icb_id:
                    raise ValidationError(
                        'NHS Trusts in England must be associated with an Integrated Care Board (ICB)!')
                if trust.health_board_id:
                    raise ValidationError('An NHS England Trust cannot be associated with a Scottish Health Board!')
                if trust.icb_id.region_id != trust.region_id:
                    raise ValidationError('The selected ICB must belong to the selected NHS Region!')
                if trust.ics_id and trust.ics_id.icb_id != trust.icb_id:
                    raise ValidationError('The selected ICS subdivision must belong to the selected ICB!')

            elif trust.health_system == 'nhs_scotland':
                if not trust.health_board_id:
                    raise ValidationError('NHS Trusts in Scotland must be associated with a Health Board!')
                if trust.icb_id or trust.ics_id:
                    raise ValidationError(
                        'An NHS Scotland Trust cannot be associated with an English'
                        ' Integrated Care Board (ICB) or Integrated Care System (ICS)!')
                if trust.health_board_id.region_id != trust.region_id:
                    raise ValidationError('The selected Health Board must belong to the selected NHS Region!')

    @api.constrains('state', 'health_system')
    def _check_state_health_system(self):
        for trust in self:
            if trust.health_system == 'nhs_scotland' and trust.state == 'special_measures':
                raise ValidationError('NHS Scotland Trusts cannot be placed in Special Measures!')

    @api.onchange('health_system')
    def _onchange_health_system(self):
        self.region_id = False
        self.icb_id = False
        self.ics_id = False
        self.health_board_id = False
        if self.health_system == 'nhs_england':
            return {'domain': {
                'region_id': [('health_system', '=', 'nhs_england')],
                'trust_type_id': [('health_system', 'in', ('nhs_england', 'both'))]
            }}
        elif self.health_system == 'nhs_scotland':
            self.foundation_trust = False
            self.foundation_authorised_date = False
            self.companies_house_number = False
            return {'domain': {
                'region_id': [('health_system', '=', 'nhs_scotland')],
                'trust_type_id': [('health_system', 'in', ('nhs_scotland', 'both'))]
            }}

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.state_id and self.state_id.country_id != self.country_id:
            self.state_id = False

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id.country_id and self.country_id != self.state_id.country_id:
            self.country_id = self.state_id.country_id

    @api.onchange('region_id')
    def _onchange_region_id(self):
        self.icb_id = False
        self.ics_id = False
        self.health_board_id = False
        if self.region_id:
            if self.health_system == 'nhs_england':
                return {'domain': {'icb_id': [('region_id', '=', self.region_id.id)]}}
            elif self.health_system == 'nhs_scotland':
                return {'domain': {'health_board_id': [('region_id', '=', self.region_id.id)]}}

    @api.onchange('icb_id')
    def _onchange_icb_id(self):
        self.ics_id = False
        domain = {'ics_id': [('id', '=', False)]}
        if self.icb_id:
            if self.icb_id.region_id:
                self.region_id = self.icb_id.region_id
            domain['ics_id'] = [('icb_id', '=', self.icb_id.id)]
            domain['region_id'] = [('id', '=', self.icb_id.region_id.id)]
        else:
            if self.health_system == 'nhs_england':
                domain['region_id'] = [('health_system', '=', 'nhs_england')]
        return {'domain': domain}

    @api.onchange('health_board_id')
    def _onchange_health_board_id(self):
        domain = {}
        if self.health_board_id:
            if self.health_board_id.region_id:
                self.region_id = self.health_board_id.region_id
            domain['region_id'] = [('id', '=', self.health_board_id.region_id.id)]
        else:
            if self.health_system == 'nhs_scotland':
                domain['region_id'] = [('health_system', '=', 'nhs_scotland')]
        return {'domain': domain}

    @api.depends('board_member_ids')
    def _compute_board_member_count(self):
        for trust in self:
            trust.board_member_count = len(trust.board_member_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'ods_code' in vals and vals['ods_code']:
                vals['ods_code'] = vals['ods_code'].upper()
        return super(NhsTrust, self).create(vals_list)

    def write(self, vals):
        if 'state' in vals:
            new_state = vals['state']
            allowed_transitions = {
                'draft': ['under_review'],
                'under_review': ['active'],
                'active': ['special_measures', 'suspended', 'merging', 'dissolved'],
                'special_measures': ['active', 'suspended', 'merging', 'dissolved'],
                'suspended': ['active', 'special_measures', 'merging', 'dissolved'],
                'merging': ['dissolved'],
                'dissolved': [],
            }
            for record in self:
                if new_state != record.state:
                    if record.state == 'dissolved':
                        raise ValidationError("The Trust is dissolved and in a final terminal state. No further state transitions are allowed.")
                    allowed = allowed_transitions.get(record.state or 'draft', [])
                    health_system = vals.get('health_system', record.health_system)
                    if health_system == 'nhs_scotland':
                        allowed = [s for s in allowed if s != 'special_measures']
                    if new_state not in allowed:
                        raise ValidationError(
                            f"Invalid state transition from '{record.state}' to '{new_state}'! "
                            f"Permitted transitions from '{record.state}' are: {', '.join(allowed)}."
                        )
            if not self.env.context.get('approved_state_change'):
                raise UserError(
                    'Direct updates to workflow state are blocked! Please use the "Change State" action button.')
        if 'ods_code' in vals and vals['ods_code']:
            vals['ods_code'] = vals['ods_code'].upper()
        return super(NhsTrust, self).write(vals)

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if 'name' not in default:
            for trust, vals in zip(self, vals_list):
                vals['name'] = self.env._("%s (copy)", trust.name)
        if 'ods_code' not in default:
            for trust, vals in zip(self, vals_list):
                base_code = (trust.ods_code or '').upper()
                import random
                import string
                chars = string.ascii_uppercase + string.digits
                new_code = base_code
                found = False
                for _ in range(100):
                    if len(base_code) < 5:
                        new_code = (base_code + random.choice(chars))[:5]
                    else:
                        new_code = base_code[:4] + random.choice(chars)

                    if not self.env['nhs.trust'].search_count([('ods_code', '=', new_code)]):
                        found = True
                        break

                if not found:
                    for _ in range(100):
                        new_code = ''.join(random.choices(chars, k=5))
                        if not self.env['nhs.trust'].search_count([('ods_code', '=', new_code)]):
                            found = True
                            break

                vals['ods_code'] = new_code
        return vals_list

    def action_open_state_change_wizard(self):
        self.ensure_one()
        ctx = dict(self.env.context)
        ctx['default_trust_id'] = self.id
        return {
            'name': 'NHS Trust State Transition',
            'type': 'ir.actions.act_window',
            'res_model': 'nhs.trust.state.change.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('odoo_nhs_trust_management.view_nhs_trust_state_change_wizard_form').id,
            'target': 'new',
            'context': ctx
        }

    def unlink(self):
        for trust in self:
            if trust.state != 'draft':
                raise UserError(
                    'You cannot delete an NHS Trust that is not in Draft state! Only Draft trusts can be deleted.')
            if 'site_ids' in self._fields and trust.site_ids:
                raise UserError(
                    f"You cannot delete NHS Trust '{trust.name}' because it still has associated sites."
                    f" Please remove or transfer all sites first.")
        return super(NhsTrust, self).unlink()
