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
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain


class PurchaseOrder(models.Model):
    """Extends purchase.order with pharma approval state and AVL enforcement."""
    _inherit = 'purchase.order'

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
        copy=False,
        tracking=True,
        readonly=True,
        help='QA Director who approved the purchase order.',
    )
    pharma_approval_date = fields.Date(
        copy=False,
        tracking=True,
        readonly=True,
        help='Date QA approved the purchase order.',
    )
    pharma_notes = fields.Text(
        string='Pharma / QA Notes',
        help='QA remarks or conditions attached to this PO.',
    )
    approved_vendor_ids = fields.Many2many(
        comodel_name='res.partner',
        compute='_compute_approved_vendor_ids',
        string='Approved Vendors',
        help='Vendors approved on the AVL, plus vendors marked Not Qualified.',
    )
    is_vendor_not_qualified = fields.Boolean(
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
        """Compute products allowed for the selected vendor (AVL approved or Vendor Qualification assigned).

        No vendor means no allowed product: lines can only be filled once the
        vendor is known, and then only with the materials that vendor is
        qualified to supply.
        """
        for order in self:
            if not order.partner_id:
                order.allowed_product_ids = self.env['product.product'].browse()
                continue

            # 1. Approved products from AVL
            approved_avls = self.env['pharma.avl'].search([
                ('vendor_id', '=', order.partner_id.id),
                ('status', '=', 'approved'),
            ])
            approved_tmpl_ids = approved_avls.mapped('product_id').ids

            # 2. Assigned products from Vendor Qualification (Approved or Not
            #    Qualified status — a Not Qualified vendor stays selectable but
            #    raises the warning banner on the PO).
            qualifications = self.env['pharma.vendor.qualification'].search([
                ('vendor_id', '=', order.partner_id.id),
                ('status', 'in', ('approved', 'not_qualified')),
            ])
            qualified_tmpl_ids = qualifications.mapped('product_ids').ids

            total_tmpl_ids = list(set(approved_tmpl_ids + qualified_tmpl_ids))

            if total_tmpl_ids:
                order.allowed_product_ids = self.env['product.product'].search([
                    ('product_tmpl_id', 'in', total_tmpl_ids)
                ])
            else:
                order.allowed_product_ids = self.env['product.product'].browse()

    def _get_product_catalog_domain(self):
        """Keep the product catalog in step with the qualified-vendor product list."""
        return super()._get_product_catalog_domain() & Domain('id', 'in', self.allowed_product_ids.ids)

    @api.depends('company_id')
    def _compute_approved_vendor_ids(self):
        """Vendors approved on the AVL or marked Not Qualified; the same for every order."""
        vendors = (
            self.env['pharma.avl'].search([('status', '=', 'approved')]).vendor_id
            | self.env['pharma.vendor.qualification'].search([('status', '=', 'not_qualified')]).vendor_id
        )
        self.approved_vendor_ids = vendors

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
        # The workflow actions write these elevated after their group check. A
        # context key would not do: any RPC client can send one.
        protected_fields = {'pharma_approval_state', 'pharma_approved_by', 'pharma_approval_date'}
        if protected_fields.intersection(vals) and not self.env.su:
            raise UserError(self.env._('Pharma PO approval fields can only be changed by workflow actions.'))
        return super().write(vals)

    def _check_group(self, group_xmlid, message):
        """Check whether the current user is in a given security group."""
        if not self.env.user.has_group(group_xmlid):
            raise UserError(message)

    def action_submit_pharma_approval(self):
        """Procurement submits the PO for QA Director review."""
        self._check_group(
            'pharmaceutical_base.group_pharma_procurement',
            self.env._('Only Pharma Procurement users can submit POs for QA approval.'),
        )
        for order in self:
            if order.pharma_approval_state != 'draft':
                raise UserError(self.env._('Only draft POs can be submitted for QA approval.'))
            if not order.order_line:
                raise UserError(self.env._('Cannot submit a PO with no order lines.'))
            order.sudo().pharma_approval_state = 'waiting_approval'
            order.message_post(
                body=self.env._('PO submitted for QA Director approval by %s.', self.env.user.name)
            )

    def action_pharma_approve(self):
        """QA Director approves the PO after verifying the vendor's AVL entry."""
        self._check_group(
            'pharmaceutical_base.group_pharma_qa_director',
            self.env._('Only the Pharma QA Director can approve POs.'),
        )
        for order in self:
            if order.pharma_approval_state != 'waiting_approval':
                raise UserError(self.env._('Only POs waiting for approval can be approved.'))
            # AVL check — non-approved vendors are blocked here
            order._check_avl()
            order.sudo().write({
                'pharma_approval_state': 'approved',
                'pharma_approved_by': self.env.user.id,
                'pharma_approval_date': fields.Date.today(),
            })
            order.message_post(
                body=self.env._('PO approved by QA Director %s. Vendor is on the Approved Vendor List.', self.env.user.name)
            )

    def action_pharma_reject(self):
        """QA Director rejects the PO for revision and resubmission."""
        self._check_group(
            'pharmaceutical_base.group_pharma_qa_director',
            self.env._('Only the Pharma QA Director can reject POs.'),
        )
        for order in self:
            if order.pharma_approval_state != 'waiting_approval':
                raise UserError(self.env._('Only POs waiting for approval can be rejected.'))
            order.sudo().write({
                'pharma_approval_state': 'rejected',
                'pharma_approved_by': False,
                'pharma_approval_date': False,
            })
            order.message_post(
                body=self.env._('PO rejected by QA Director %s. Please revise and resubmit.', self.env.user.name)
            )

    def action_pharma_reset_draft(self):
        """Reset a rejected PO back to draft for revision."""
        self._check_group(
            'pharmaceutical_base.group_pharma_procurement',
            self.env._('Only Pharma Procurement users can reset rejected POs to draft.'),
        )
        for order in self:
            if order.pharma_approval_state != 'rejected':
                raise UserError(self.env._('Only rejected POs can be reset to draft.'))
            order.sudo().write({
                'pharma_approval_state': 'draft',
                'pharma_approved_by': False,
                'pharma_approval_date': False,
            })
            order.message_post(
                body=self.env._('PO reset to draft for revision by %s.', self.env.user.name)
            )

    def button_confirm(self):
        """Block PO confirmation unless approved, then run a final AVL check."""
        for order in self:
            if self.env.context.get('install_mode'):
                continue

            if order.pharma_approval_state != 'approved':
                raise UserError(self.env._(
                    'Purchase Order "%(order)s" must be approved by the QA Director '
                    'before it can be confirmed.\n\n'
                    'Current status: %(status)s\n\n'
                    'Please submit for QA approval first.',
                    order=order.name,
                    status=dict(order._fields['pharma_approval_state'].selection).get(
                        order.pharma_approval_state, order.pharma_approval_state),
                ))
            order._check_avl()
        return super().button_confirm()

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
                    raise UserError(self.env._(
                        'AVL Check Failed: Vendor "%(vendor)s" is not on the '
                        'Approved Vendor List for product "%(product)s".\n\n'
                        'Only approved vendors can create a Purchase Order. '
                        'This order will remain in "Waiting for Approval" until '
                        'the vendor is added to the AVL or replaced.',
                        vendor=partner.name,
                        product=product_tmpl.name,
                    ))
