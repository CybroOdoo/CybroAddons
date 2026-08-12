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

class PharmaQcSpec(models.Model):
    """QC Specification — acceptance criteria per product per testing stage."""
    _name = 'pharma.qc.spec'
    _description = 'QC Specification'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'pharma.workflow.mixin']
    _order = 'product_id, stage'
    name = fields.Char(
        string='Specification Name',
        readonly=True,
        copy=False,
        tracking=True,
        default='/',
        help='Specifies the Specification Name for this record.',
    )

    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
        domain=[('tracking', '=', 'lot')],
        help='Specifies the Product for this record. '
             'Only products tracked by lots are selectable.',
    )

    stage = fields.Selection(
        selection=[
            ('incoming', 'Incoming / Raw Material'),
            ('finished', 'Finished Goods'),
            ('ipqc', 'IPQC'),
        ],
        string='Testing Stage',
        required=True,
        tracking=True,
            help='Specifies the Testing Stage for this record.',
    )

    pharmacopoeial_ref = fields.Selection(
        selection=[
            ('bp', 'BP'),
            ('usp', 'USP'),
            ('ep', 'EP'),
            ('ip', 'IP'),
            ('inhouse', 'In-House'),
        ],
        string='Pharmacopoeial Reference',
        tracking=True,
            help='Specifies the Pharmacopoeial Reference for this record.',
    )

    version = fields.Char(
        string='Version',
        default='1.0',
        required=True,
        tracking=True,
            help='Specifies the Version for this record.',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('review', 'Under Review'),
            ('approved', 'Approved'),
            ('obsolete', 'Obsolete'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
            help='Specifies the Status for this record.',
    )

    approved_by = fields.Many2one(
        comodel_name='res.users',
        string='Approved By',
        tracking=True,
        readonly=True,
        help='Specifies the Approved By for this record.',
    )

    approval_date = fields.Date(
        string='Approval Date',
        tracking=True,
        readonly=True,
        help='Specifies the Approval Date for this record.',
    )

    effective_date = fields.Date(
        string='Valid Until Date',
        tracking=True,
        help='Date until which this specification version is active and can be used for new test orders.',
    )
    parameter_ids = fields.One2many(
        comodel_name='pharma.qc.spec.line',
        inverse_name='spec_id',
        string='Test Parameters',
            help='Specifies the Test Parameters for this record.',
    )

    notes = fields.Text(

        string='Notes / Sampling Instructions',

            help='Specifies the Notes / Sampling Instructions for this record.',
    )
    _unique_product_stage_version = models.Constraint(
        'UNIQUE(product_id, stage, version)',
        'A specification with this version already exists for this product and stage.',
    )

    @api.constrains('state', 'approved_by', 'approval_date')
    def _check_approval(self):
        """Require an approver and approval date when a specification is approved."""
        for rec in self:
            if rec.state == 'approved' and not (rec.approved_by and rec.approval_date):
                raise ValidationError(
                    _('Approved By and Approval Date are required when approving a specification.')
                )

    @api.constrains('effective_date')
    def _check_effective_date(self):
        """Executes the _check_effective_date operation."""
        for rec in self:
            if rec.effective_date and rec.effective_date < fields.Date.today():
                raise ValidationError(_("The Valid Until Date cannot be less than today."))

    @api.constrains('parameter_ids')
    def _check_parameter_ids(self):
        """Executes the _check_parameter_ids operation."""
        for rec in self:
            if not rec.parameter_ids:
                raise ValidationError(_("At least one test parameter is required to save the specification."))

    def _next_version(self, product_id, stage):
        """Compute the next whole version number for a product/stage specification."""
        if not product_id:
            return '1.0'
        existing = self.search([
            ('product_id', '=', product_id),
            ('stage', '=', stage),
        ])
        max_version = 0.0
        for rec in existing:
            try:
                max_version = max(max_version, float(rec.version))
            except (ValueError, TypeError):
                continue
        return '%.1f' % (max_version + 1.0)

    @api.onchange('product_id', 'stage')
    def _onchange_product_stage_version(self):
        """Reflect the auto-assigned version in the form as the product/stage change."""
        for rec in self:
            rec.version = rec._next_version(rec.product_id.id, rec.stage)

    @api.model_create_multi
    def create(self, vals_list):
        """Executes the create operation."""
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                product = self.env['product.template'].browse(vals.get('product_id'))
                stage = vals.get('stage', '')
                seq = self.env['ir.sequence'].next_by_code('pharma.qc.spec') or '/'
                vals['name'] = f"SPEC/{product.name}/{stage}/{seq}".upper()
            # Version is system-managed — always assign the next value.
            vals['version'] = self._next_version(vals.get('product_id'), vals.get('stage', ''))
        return super().create(vals_list)

    def action_submit_review(self):
        """Transitions the specification to the Under Review state."""
        self.write({'state': 'review'})

    def action_approve(self):
        """Approve the specification, logging the user and date."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can approve a QC specification.'),
        )
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'approval_date': fields.Date.today(),
        })

    def action_obsolete(self):
        """Mark the specification obsolete to prevent future use."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can mark a QC specification obsolete.'),
        )
        self.write({'state': 'obsolete'})

    def action_reset_draft(self):
        """Reverts the specification back to Draft state for further editing."""
        self._check_pharma_group(
            'pharmaceutical_base.group_pharma_role_qa',
            _('Only QA can reset a QC specification to draft.'),
        )
        self.write({'state': 'draft'})
