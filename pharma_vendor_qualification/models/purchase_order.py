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


class PurchaseOrder(models.Model):
    """Extends purchase.order with pharma approval state and AVL enforcement."""
    _inherit = 'purchase.order'

    # ── Unified Statusbar Field ───────────────────────────────────────────────
    pharma_po_state = fields.Selection(
        selection=[
            ('rfq', 'RFQ'),
            ('sent', 'Sent RFQ'),
            ('waiting_approval', 'Waiting for Approval'),
            ('purchase', 'PO'),
        ],
        string='Pharma Status',
        compute='_compute_pharma_po_state',
        store=True,
        copy=False,
        tracking=True,
        help='Unified purchase statusbar combining the Odoo PO state and the '
             'pharma QA approval workflow.',
    )
    # ── Pharma Approval State ─────────────────────────────────────────────────
    pharma_approval_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('waiting_approval', 'Waiting for Approval'),
            ('approved', 'QA Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Pharma Approval',
        default='draft',
        copy=False,
        tracking=True,
        help='QA review status for this purchase order.',
    )
    pharma_approved_by = fields.Many2one(
        comodel_name='res.users',
        string='Pharma Approved By',
        copy=False,
        tracking=True,
        readonly=True,
        help='Specifies the Pharma Approved By for this record.',
    )
    pharma_approval_date = fields.Date(
        string='Pharma Approval Date',
        copy=False,
        tracking=True,
        readonly=True,
        help='Specifies the Pharma Approval Date for this record.',
    )
    pharma_notes = fields.Text(
        string='Pharma / QA Notes',
        help='QA remarks or conditions attached to this PO.',
    )
    approved_vendor_ids = fields.Many2many(
        comodel_name='res.partner',
        compute='_compute_approved_vendor_ids',
        string='Approved Vendors',
        help='Specifies the Approved Vendors for this record.',
    )
    is_vendor_not_qualified = fields.Boolean(
        string='Is Vendor Not Qualified',
        compute='_compute_is_vendor_not_qualified',
        store=False,
        help='Indicates if the selected vendor is marked as Not Qualified in Vendor Qualification.',
    )
    allowed_product_ids = fields.Many2many(
        comodel_name='product.product',
        compute='_compute_allowed_product_ids',
        string='Allowed Products',
        help='Products that are allowed to be purchased from the selected vendor.',
    )

    @api.depends('partner_id')
    def _compute_is_vendor_not_qualified(self):
        """Check if the selected vendor has a Not Qualified status in Vendor Qualification."""
        for order in self:
            if order.partner_id:
                not_qual = self.env['pharma.vendor.qualification'].search([
                    ('vendor_id', '=', order.partner_id.id),
                    ('status', '=', 'not_qualified'),
                ], limit=1)
                order.is_vendor_not_qualified = bool(not_qual)
            else:
                order.is_vendor_not_qualified = False

    @api.depends('partner_id')
    def _compute_allowed_product_ids(self):
        """Compute products allowed for the selected vendor (AVL approved or Vendor Qualification assigned)."""
        for order in self:
            if not order.partner_id:
                order.allowed_product_ids = self.env['product.product'].search([])
                continue

            # 1. Approved products from AVL
            approved_avls = self.env['pharma.avl'].search([
                ('vendor_id', '=', order.partner_id.id),
                ('status', '=', 'approved'),
            ])
            approved_tmpl_ids = approved_avls.mapped('product_id').ids

            # 2. Assigned products from Vendor Qualification (Not Qualified status)
            qualifications = self.env['pharma.vendor.qualification'].search([
                ('vendor_id', '=', order.partner_id.id),
                ('status', '=', 'not_qualified'),
            ])
            not_qual_tmpl_ids = qualifications.mapped('product_ids').ids

            total_tmpl_ids = list(set(approved_tmpl_ids + not_qual_tmpl_ids))

            if total_tmpl_ids:
                order.allowed_product_ids = self.env['product.product'].search([
                    ('product_tmpl_id', 'in', total_tmpl_ids)
                ])
            else:
                order.allowed_product_ids = self.env['product.product'].browse()

    def _compute_approved_vendor_ids(self):
        """Assign vendors who are approved in the AVL or have a Not Qualified status."""
        for order in self:
            avls = self.env['pharma.avl'].search([('status', '=', 'approved')])
            not_qual = self.env['pharma.vendor.qualification'].search([('status', '=', 'not_qualified')])
            order.approved_vendor_ids = avls.mapped('vendor_id') | not_qual.mapped('vendor_id')

    # ── Compute Unified Statusbar ─────────────────────────────────────────────
    @api.depends('state', 'pharma_approval_state')
    def _compute_pharma_po_state(self):
        """Derive the 4-stage pharma statusbar from Odoo state and approval state."""
        for order in self:
            native = order.state
            pharma = order.pharma_approval_state

            if native in ('purchase', 'done'):
                order.pharma_po_state = 'purchase'
            elif pharma == 'waiting_approval':
                order.pharma_po_state = 'waiting_approval'
            elif native == 'sent':
                order.pharma_po_state = 'sent'
            else:
                order.pharma_po_state = 'rfq'

    def write(self, vals):
        """Restrict modifications to pharma approval fields to workflow actions only."""
        protected_fields = {'pharma_approval_state', 'pharma_approved_by', 'pharma_approval_date'}
        if protected_fields.intersection(vals) and not self.env.context.get('pharma_po_workflow_action'):
            raise UserError(_('Pharma PO approval fields can only be changed by workflow actions.'))
        return super().write(vals)

    def _check_group(self, group_xmlid, message):
        """Check whether the current user is in a given security group."""
        if not self.env.user.has_group(group_xmlid):
            raise UserError(message)

    # ── Submit for QA Approval ────────────────────────────────────────────────
    def action_submit_pharma_approval(self):
        """Procurement submits the PO for QA Director review."""
        self._check_group(
            'pharmaceutical_base.group_pharma_procurement',
            _('Only Pharma Procurement users can submit POs for QA approval.'),
        )
        for order in self:
            if order.pharma_approval_state != 'draft':
                raise UserError(_('Only draft POs can be submitted for QA approval.'))
            if not order.order_line:
                raise UserError(_('Cannot submit a PO with no order lines.'))
            order.with_context(pharma_po_workflow_action=True).pharma_approval_state = 'waiting_approval'
            order.message_post(
                body=_('PO submitted for QA Director approval by %s.') % self.env.user.name
            )

    # ── QA Director Approve ───────────────────────────────────────────────────
    def action_pharma_approve(self):
        """QA Director approves the PO after verifying the vendor's AVL entry."""
        self._check_group(
            'pharmaceutical_base.group_pharma_qa_director',
            _('Only the Pharma QA Director can approve POs.'),
        )
        for order in self:
            if order.pharma_approval_state != 'waiting_approval':
                raise UserError(_('Only POs waiting for approval can be approved.'))
            # AVL check — non-approved vendors are blocked here
            order._check_avl()
            order.with_context(pharma_po_workflow_action=True).write({
                'pharma_approval_state': 'approved',
                'pharma_approved_by': self.env.user.id,
                'pharma_approval_date': fields.Date.today(),
            })
            order.message_post(
                body=_('PO approved by QA Director %s. Vendor is on the Approved Vendor List.') % self.env.user.name
            )

    # ── QA Director Reject ────────────────────────────────────────────────────
    def action_pharma_reject(self):
        """QA Director rejects the PO for revision and resubmission."""
        self._check_group(
            'pharmaceutical_base.group_pharma_qa_director',
            _('Only the Pharma QA Director can reject POs.'),
        )
        for order in self:
            if order.pharma_approval_state != 'waiting_approval':
                raise UserError(_('Only POs waiting for approval can be rejected.'))
            order.with_context(pharma_po_workflow_action=True).write({
                'pharma_approval_state': 'rejected',
                'pharma_approved_by': False,
                'pharma_approval_date': False,
            })
            order.message_post(
                body=_('PO rejected by QA Director %s. Please revise and resubmit.') % self.env.user.name
            )

    # ── Reset to Draft (after rejection) ─────────────────────────────────────
    def action_pharma_reset_draft(self):
        """Reset a rejected PO back to draft for revision."""
        self._check_group(
            'pharmaceutical_base.group_pharma_procurement',
            _('Only Pharma Procurement users can reset rejected POs to draft.'),
        )
        for order in self:
            if order.pharma_approval_state != 'rejected':
                raise UserError(_('Only rejected POs can be reset to draft.'))
            order.with_context(pharma_po_workflow_action=True).write({
                'pharma_approval_state': 'draft',
                'pharma_approved_by': False,
                'pharma_approval_date': False,
            })
            order.message_post(
                body=_('PO reset to draft for revision by %s.') % self.env.user.name
            )

    # ── Block Confirm Unless QA Approved ─────────────────────────────────────
    def button_confirm(self):
        """Block PO confirmation unless approved, then run a final AVL check."""
        for order in self:
            if self.env.su or self.env.context.get('install_mode'):
                continue

            if order.pharma_approval_state != 'approved':
                raise UserError(_(
                    'Purchase Order "%s" must be approved by the QA Director '
                    'before it can be confirmed.\n\n'
                    'Current status: %s\n\n'
                    'Please submit for QA approval first.'
                ) % (order.name, dict(order._fields['pharma_approval_state'].selection).get(
                    order.pharma_approval_state, order.pharma_approval_state
                )))
            order._check_avl()
        return super().button_confirm()

    # ── AVL Check ─────────────────────────────────────────────────────────────
    def _check_avl(self):
        """Verify each pharma line's vendor is approved on the AVL or has a Not Qualified qualification."""
        partner = self.partner_id
        for line in self.order_line:
            product_tmpl = line.product_id.product_tmpl_id
            if not product_tmpl.product_type_pharma:
                continue
            avl = self.env['pharma.avl'].search([
                ('product_id', '=', product_tmpl.id),
                ('vendor_id', '=', partner.id),
                ('status', '=', 'approved'),
            ], limit=1)
            if not avl:
                not_qual = self.env['pharma.vendor.qualification'].search([
                    ('vendor_id', '=', partner.id),
                    ('status', '=', 'not_qualified'),
                ], limit=1)
                if not not_qual:
                    raise UserError(_(
                        'AVL Check Failed: Vendor "%(vendor)s" is not on the '
                        'Approved Vendor List for product "%(product)s".\n\n'
                        'Only approved vendors can create a Purchase Order. '
                        'This order will remain in "Waiting for Approval" until '
                        'the vendor is added to the AVL or replaced.',
                        vendor=partner.name,
                        product=product_tmpl.name,
                    ))
