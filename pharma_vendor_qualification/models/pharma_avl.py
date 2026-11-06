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

# Set only by the workflow buttons and by qualifying the vendor, which write
# them elevated after their own checks. Written directly they would put any
# vendor on the list a purchase order is checked against.
_AVL_WORKFLOW_FIELDS = frozenset({'status', 'approval_date', 'approved_by'})
# Editable while the entry is under review, as in the form.
_AVL_KEY_FIELDS = frozenset({'product_id', 'vendor_id'})


class PharmaAVL(models.Model):
    """Approved Vendor List — one approved product-vendor pair per record."""
    _name = 'pharma.avl'
    _description = 'Approved Vendor List'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_names_search = ['product_id.name', 'vendor_id.name']
    _order = 'product_id, status, vendor_id'

    product_id = fields.Many2one(
        comodel_name='product.template',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
        help='Material the vendor is approved to supply.',
    )
    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        required=True,
        domain=[('supplier_rank', '>', 0)],
        ondelete='restrict',
        index=True,
        tracking=True,
        help='Vendor approved for the material.',
    )
    status = fields.Selection(
        selection=[
            ('under_review', 'Under Review'),
            ('pending_approval', 'Waiting for Approval'),
            ('approved', 'Approved'),
            ('blocked', 'Blocked'),
        ],
        default='under_review',
        required=True,
        tracking=True,
        readonly=True,
        help='Under Review, Waiting for Approval, Approved or Blocked. Only Approved entries allow purchase orders.',
    )
    approval_date = fields.Date(
        tracking=True,
        readonly=True,
        help='Date the vendor was approved. Auto-filled on QA Director approval.',
    )
    approved_by = fields.Many2one(
        comodel_name='res.users',
        tracking=True,
        readonly=True,
        help='QA Director who approved this vendor.',
    )
    expiry_date = fields.Date(
        string='Approval Expiry Date',
        tracking=True,
        help='Date the vendor approval expires and must be re-evaluated.',
    )
    vendor_item_code = fields.Char(
        string="Vendor's Item Code",
        help="Vendor's own part number or code for this material.",
    )
    lead_time_days = fields.Integer(
        string='Lead Time (Days)',
        help='Typical delivery lead time in calendar days.',
    )
    notes = fields.Text(
        help='Any additional qualification remarks or special conditions.',
    )

    _unique_product_vendor = models.Constraint(
        'UNIQUE(product_id, vendor_id)',
        "A vendor can appear only once per product in the Approved Vendor List.",
    )

    @api.depends('product_id', 'vendor_id')
    def _compute_display_name(self):
        """Generates a composite display name using the product name and vendor name."""
        for rec in self:
            product = rec.product_id.name or ''
            vendor = rec.vendor_id.name or ''
            rec.display_name = f'{product} / {vendor}' if product or vendor else self.env._('New AVL')

    @api.model_create_multi
    def create(self, vals_list):
        """Refuse an entry created already approved or blocked."""
        if not self.env.su and any(
                vals.get('status', 'under_review') != 'under_review'
                or vals.get('approval_date') or vals.get('approved_by')
                for vals in vals_list):
            raise UserError(self.env._(
                'A new AVL entry starts Under Review; the QA Director approves it.'))
        return super().create(vals_list)

    def write(self, vals):
        """Keep the approval to the workflow and fix the vendor and product once reviewed."""
        if not self.env.su:
            if _AVL_WORKFLOW_FIELDS & set(vals):
                raise UserError(self.env._(
                    'The status and approval of an AVL entry are set by its '
                    'workflow buttons only.'))
            if _AVL_KEY_FIELDS & set(vals) and any(
                    rec.status != 'under_review' for rec in self):
                raise UserError(self.env._(
                    'The vendor and product of an AVL entry can only change '
                    'while it is Under Review.'))
        return super().write(vals)

    def _check_group(self, group_xmlid, message):
        """Check whether the current user is in a given security group."""
        if not self.env.user.has_group(group_xmlid):
            raise UserError(message)

    def action_submit_review(self):
        """Procurement submits the AVL entry for QA Director review. Allowed from: under_review"""
        self._check_group(
            'pharmaceutical_base.group_pharma_procurement',
            self.env._('Only Pharma Procurement users can submit AVL entries for approval.'),
        )
        for rec in self:
            if rec.status != 'under_review':
                raise UserError(self.env._('Only entries under review can be submitted for approval.'))
            rec.sudo().status = 'pending_approval'
            rec.message_post(body=self.env._('Submitted for QA Director approval by %s.', self.env.user.name))

    def action_submit(self):
        """Alias for action_submit_review to transition the entry for QA approval."""
        return self.action_submit_review()

    def action_approve(self):
        """QA Director approves the vendor, stamping approval date and approver."""
        self._check_group(
            'pharmaceutical_base.group_pharma_qa_director',
            self.env._('Only the Pharma QA Director can approve AVL entries.'),
        )
        for rec in self:
            if rec.status != 'pending_approval':
                raise UserError(self.env._('Only entries waiting for approval can be approved.'))
            rec.sudo().write({
                'status': 'approved',
                'approval_date': fields.Date.today(),
                'approved_by': self.env.user.id,
            })
            rec.message_post(body=self.env._('Vendor approved by QA Director %s.', self.env.user.name))

    def action_block(self):
        """QA Director blocks the vendor from any state."""
        self._check_group(
            'pharmaceutical_base.group_pharma_qa_director',
            self.env._('Only the Pharma QA Director can block AVL entries.'),
        )
        for rec in self:
            rec.sudo().write({
                'status': 'blocked',
                'approval_date': False,
                'approved_by': False,
            })
            rec.message_post(body=self.env._('Vendor blocked by %s.', self.env.user.name))

    def action_reset(self):
        """Reset back to Under Review (for corrections before re-submission). Restricted to: group_pharma_qa_director"""
        self._check_group(
            'pharmaceutical_base.group_pharma_qa_director',
            self.env._('Only the Pharma QA Director can reset AVL entries.'),
        )
        for rec in self:
            rec.sudo().write({
                'status': 'under_review',
                'approval_date': False,
                'approved_by': False,
            })
            rec.message_post(body=self.env._('Reset to Under Review by %s.', self.env.user.name))
