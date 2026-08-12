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


class PharmaAVL(models.Model):
    """Approved Vendor List — one approved product-vendor pair per record."""
    _name = 'pharma.avl'
    _description = 'Approved Vendor List'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'product_id, status, vendor_id'
    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
            help='Specifies the Product for this record.',
    )

    vendor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor',
        required=True,
        domain=[('supplier_rank', '>', 0)],
        ondelete='restrict',
        index=True,
        tracking=True,
            help='Specifies the Vendor for this record.',
    )

    status = fields.Selection(
        selection=[
            ('under_review', 'Under Review'),
            ('pending_approval', 'Waiting for Approval'),
            ('approved', 'Approved'),
            ('blocked', 'Blocked'),
        ],
        string='Status',
        default='under_review',
        required=True,
        tracking=True,
        readonly=True,
            help='Specifies the Status for this record.',
    )
    approval_date = fields.Date(
        string='Approval Date',
        tracking=True,
        readonly=True,
        help='Date the vendor was approved. Auto-filled on QA Director approval.',
    )

    approved_by = fields.Many2one(
        comodel_name='res.users',
        string='Approved By',
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
        string='Notes',
        help='Any additional qualification remarks or special conditions.',
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
            help='Specifies the Display Name for this record.',
    )

    @api.depends('product_id', 'vendor_id')
    def _compute_display_name(self):
        """Generates a composite display name using the product name and vendor name."""
        for rec in self:
            product = rec.product_id.name or ''
            vendor = rec.vendor_id.name or ''
            rec.display_name = f'{product} / {vendor}' if product or vendor else _('New AVL')
    _sql_constraints = [
        (
            'unique_product_vendor',
            'UNIQUE(product_id, vendor_id)',
            'A vendor can appear only once per product in the Approved Vendor List.',
        ),
    ]

    def _check_group(self, group_xmlid, message):
        """Check whether the current user is in a given security group."""
        if not self.env.user.has_group(group_xmlid):
            raise UserError(message)

    def action_submit_review(self):
        """Procurement submits the AVL entry for QA Director review. Allowed from: under_review"""
        self._check_group(
            'pharmaceutical_base.group_pharma_procurement',
            _('Only Pharma Procurement users can submit AVL entries for approval.'),
        )
        for rec in self:
            if rec.status != 'under_review':
                raise UserError(_('Only entries under review can be submitted for approval.'))
            rec.with_context(pharma_avl_workflow_action=True).status = 'pending_approval'
            rec.message_post(body=_('Submitted for QA Director approval by %s.') % self.env.user.name)

    def action_submit(self):
        """Alias for action_submit_review to transition the entry for QA approval."""
        return self.action_submit_review()

    def action_approve(self):
        """QA Director approves the vendor, stamping approval date and approver."""
        self._check_group(
            'pharmaceutical_base.group_pharma_qa_director',
            _('Only the Pharma QA Director can approve AVL entries.'),
        )
        for rec in self:
            if rec.status != 'pending_approval':
                raise UserError(_('Only entries waiting for approval can be approved.'))
            rec.with_context(pharma_avl_workflow_action=True).write({
                'status': 'approved',
                'approval_date': fields.Date.today(),
                'approved_by': self.env.user.id,
            })
            rec.message_post(body=_('Vendor approved by QA Director %s.') % self.env.user.name)

    def action_block(self):
        """QA Director blocks the vendor from any state."""
        self._check_group(
            'pharmaceutical_base.group_pharma_qa_director',
            _('Only the Pharma QA Director can block AVL entries.'),
        )
        for rec in self:
            rec.with_context(pharma_avl_workflow_action=True).write({
                'status': 'blocked',
                'approval_date': False,
                'approved_by': False,
            })
            rec.message_post(body=_('Vendor blocked by %s.') % self.env.user.name)

    def action_reset(self):
        """Reset back to Under Review (for corrections before re-submission). Restricted to: group_pharma_qa_director"""
        self._check_group(
            'pharmaceutical_base.group_pharma_qa_director',
            _('Only the Pharma QA Director can reset AVL entries.'),
        )
        for rec in self:
            rec.with_context(pharma_avl_workflow_action=True).write({
                'status': 'under_review',
                'approval_date': False,
                'approved_by': False,
            })
            rec.message_post(body=_('Reset to Under Review by %s.') % self.env.user.name)
