# -*- coding: utf-8 -*-
#############################################################################
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

from datetime import timedelta
from odoo import api, fields, models
from odoo.orm.table_objects import Constraint
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError



class OilLeaseAgreement(models.Model):
    """
    Model for managing oil and gas lease agreements between property owners (lessors) 
    and operators (lessees). Tracks land details, technical limits, and renewals.
    """
    _name = 'oil.lease.agreement'
    _description = 'Lease Agreement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _license_number_unique = Constraint(
        'UNIQUE(license_number, company_id)',
        'The License Number must be unique per company!'
    )
    _survey_number_unique = Constraint(
        'UNIQUE(survey_number, company_id)',
        'The Survey Number must be unique per company!'
    )


    name = fields.Char(string='Lease Reference', required=True, copy=False,
                       readonly=True, default=lambda self: _('New'),
                       help="Enter the lease Reference.")
    lessor_id = fields.Many2one(
        'res.partner',
        string='Property Owner',
        required=True,
        tracking=True,
        help="The person or company that owns the land or asset and grants the lease.")
    lessee_id = fields.Many2one(
        'res.partner',
        string='Lease Holder',
        required=True,
        default=lambda self: self.env.company.partner_id,
        tracking=True,
        help="The person or company that receives and operates under the lease.")

    start_date = fields.Date(string='Start Date', required=True, tracking=True,
                             help="Select the date for start Date.")
    end_date = fields.Date(string='End Date', required=True, tracking=True,
                           help="Select the date for end Date.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated')
    ], string='Status', default='draft', tracking=True,
        help="Choose the status.")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Select the company.")

    description = fields.Text(string='Description',
                              help="Enter the description.")

    # Location / Land Details
    land_type = fields.Selection([
        ('onshore', 'Onshore'),
        ('offshore', 'Offshore')
    ], string='Land Type', tracking=True,
        help="Choose the land Type.")
    latitude = fields.Float(string='Latitude', digits=(10, 7),
                            help="Enter the latitude.")
    longitude = fields.Float(string='Longitude', digits=(10, 7),
                             help="Enter the longitude.")
    acreage = fields.Float(string='Acreage', help="Total lease area in acres.")
    survey_number = fields.Char(string='Survey Number',
                                help="Government land record number.")
    # License/Permit Details
    license_number = fields.Char(string='License Number',
                                 help="Government issued license number.")
    permit_number = fields.Char(string='Permit Number',
                                help="Drilling or operation permit number.")

    # Status Tracking
    activation_date = fields.Date(string='Activation Date', readonly=True,
                                  help="Select the date for activation Date.")
    termination_reason = fields.Text(string='Termination Reason',
                                     help="Enter the termination Reason.")
    renewal_option = fields.Boolean(string='Renewal Option Available',
                                    help="Enable this when renewal Option Available applies.")
    renewal_date = fields.Date(string='Renewed End Date',
                               help="Select the date for renewed End Date.")

    # Technical Details
    estimated_reserves = fields.Float(string='Estimated Reserves',
                                      help="Estimated oil/gas reserves in barrels/MCF.")
    production_limit = fields.Float(string='Production Limit',
                                    help="Allowed production limit per period.")
    water_cut_limit = fields.Float(string='Water Cut Limit',
                                   help="Maximum allowable water ratio.")
    gas_ratio_limit = fields.Float(string='Gas-Oil Ratio Limit',
                                   help="Maximum allowable gas-oil ratio.")

    # Documents
    agreement_document = fields.Binary(string='Lease Contract', attachment=True,
                                       help="Upload the lease Contract.")
    map_attachment = fields.Binary(string='Lease Map', attachment=True,
                                   help="Upload the lease Map.")
    document_ids = fields.Many2many('ir.attachment', string='Related Documents',
                                    help="Additional documents related to this lease.")
    reservoir_ids = fields.One2many(
        'oil.reservoir',
        'lease_id',
        string='Linked Reservoirs',
        help="All reservoirs currently associated with this lease."
    )
    reservoir_count = fields.Integer(string='Reservoirs',
                                     compute='_compute_reservoir_count',
                                     help="Number of reservoirs linked to this lease agreement.")

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assigns a unique sequence number to new lease records and syncs initial state.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.lease.agreement') or _('New')
        records = super().create(vals_list)
        records._sync_date_driven_state()
        return records

    def write(self, vals):
        """
        Overrides write to sync state if date-related fields change.
        """
        result = super().write(vals)
        tracked_fields = {'start_date', 'end_date', 'renewal_option',
                          'renewal_date', 'state'}
        if tracked_fields.intersection(vals):
            self._sync_date_driven_state()
        return result

    @api.constrains('start_date', 'end_date', 'renewal_option', 'renewal_date')
    def _check_lease_dates(self):
        """
        Validates logical consistency of start, end, and renewal dates.
        """
        for record in self:
            if record.start_date and record.end_date and record.end_date < record.start_date:
                raise ValidationError(
                    _("End Date must be on or after the Start Date."))
            if record.renewal_option and not record.renewal_date:
                raise ValidationError(
                    _("Set a Renewed End Date when Renewal Option Available is enabled."))
            if record.renewal_date and record.end_date and record.renewal_date <= record.end_date:
                raise ValidationError(
                    _("Renewed End Date must be later than the current End Date."))

    @api.constrains('license_number', 'survey_number', 'company_id')
    def _check_uniqueness(self):
        """
        Python-level uniqueness check for license and survey numbers (fallback for SQL).
        """
        for record in self:
            if record.license_number:
                domain = [('license_number', '=', record.license_number),
                          ('id', '!=', record.id),
                          ('company_id', '=', record.company_id.id)]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        _("The License Number '%s' must be unique per company!",
                          record.license_number))
            if record.survey_number:
                domain = [('survey_number', '=', record.survey_number),
                          ('id', '!=', record.id),
                          ('company_id', '=', record.company_id.id)]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        _("The Survey Number '%s' must be unique per company!",
                          record.survey_number))

    @api.onchange('renewal_option')
    def _onchange_renewal_option(self):
        """
        Clears the renewal date if the renewal option is disabled.
        """
        if not self.renewal_option:
            self.renewal_date = False

    def _sync_date_driven_state(self):
        """
        Automatically updates the 'state' field based on today's date vs end date.
        """
        today = fields.Date.today()
        for record in self:
            if record.state in ('draft', 'terminated'):
                continue
            new_state = 'expired' if record.end_date and record.end_date < today else 'active'
            if new_state != record.state:
                super(OilLeaseAgreement, record).write({'state': new_state})

    def action_activate(self):
        """
        Activates a draft lease agreement.
        """
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Only draft leases can be activated."))
            record.write({
                'state': 'active',
                'activation_date': fields.Date.today()
            })
            record._sync_date_driven_state()

    def action_terminate(self):
        """
        Terminates an active lease agreement.
        """
        for record in self:
            if record.state != 'active':
                raise UserError(_("Only active leases can be terminated."))
            record.write({'state': 'terminated'})

    def action_set_to_draft(self):
        """
        Resets a lease agreement to 'Draft' state.
        """
        for record in self:
            record.write({'state': 'draft'})

    def action_renew(self):
        """
        Renews an existing lease using the renewal date.
        """
        for record in self:
            if not record.renewal_option:
                raise UserError(
                    _("Enable Renewal Option Available before renewing the lease."))
            if not record.renewal_date:
                raise UserError(
                    _("Set a Renewed End Date before renewing the lease."))
            if record.renewal_date <= record.end_date:
                raise UserError(
                    _("Renewed End Date must be later than the current End Date."))

            record.write({
                'end_date': record.renewal_date,
                'state': 'active',
                'renewal_option': False,
                'renewal_date': False,
            })

    def _compute_reservoir_count(self):
        """
        Calculates the number of reservoirs associated with this lease agreement.
        """
        for record in self:
            record.reservoir_count = len(record.reservoir_ids)

    def action_open_reservoirs(self):
        """
        Returns an action to view all reservoirs linked to this lease agreement.
        """
        self.ensure_one()
        action = self.env.ref('oil_erp_reservoir.action_oil_reservoir').read()[
            0]
        action['domain'] = [('id', 'in', self.reservoir_ids.ids)]
        action['context'] = {'default_lease_id': self.id}
        return action

    @api.model
    def _cron_check_lease_expiry(self):
        """Scheduled action: expire active leases past end_date and
        notify related parties. Also cancels/expires related contracts
        and warns on related royalties."""
        today = fields.Date.today()
        upcoming = today + timedelta(days=7)

        # --- Send reminders for leases expiring within 7 days ---
        expiring_soon = self.search([
            ('state', '=', 'active'),
            ('end_date', '>=', today),
            ('end_date', '<=', upcoming),
        ])
        for rec in expiring_soon:
            if rec.lessor_id and rec.lessor_id.email:
                self.env['mail.mail'].sudo().create({
                    'subject': _('Lease Expiry Reminder - %s', rec.name),
                    'email_to': rec.lessor_id.email,
                    'body_html': _(
                        '<p>Dear %(name)s,</p>'
                        '<p>Lease agreement <strong>%(lease)s</strong> '
                        'is expiring on <strong>%(date)s</strong>.</p>'
                        '<p>Please take the necessary steps.</p>',
                        name=rec.lessor_id.name,
                        lease=rec.name,
                        date=rec.end_date,
                    ),
                    'auto_delete': True,
                }).send()

        # --- Expire leases that are past end_date ---
        expired = self.search([
            ('state', '=', 'active'),
            ('end_date', '<', today),
        ])
        for rec in expired:
            rec.write({'state': 'expired'})
            rec.message_post(
                body=_("Lease automatically expired on %s.", today),
                message_type='notification')

            # Expire related active contracts (if module installed)
            if 'oil.contract' in self.env:
                contracts = self.env['oil.contract'].search([
                    ('lease_id', '=', rec.id),
                    ('state', 'in', ('draft', 'confirmed')),
                ])
                for contract in contracts:
                    contract.write({'state': 'expired'})
                    contract.message_post(
                        body=_("Contract expired because lease '%s' "
                               "expired.", rec.name),
                        message_type='notification')

            # Post warning on related confirmed royalties
            # (if module installed)
            if 'oil.royalty' in self.env:
                royalties = self.env['oil.royalty'].search([
                    ('lease_id', '=', rec.id),
                    ('state', '=', 'confirmed'),
                ])
                for royalty in royalties:
                    royalty.message_post(
                        body=_("Warning: Lease Agreement '%s' has "
                               "expired. Please review this royalty.",
                               rec.name),
                        message_type='notification')
