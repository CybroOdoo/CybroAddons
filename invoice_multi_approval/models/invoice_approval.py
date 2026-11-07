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
#############################################################################
from odoo import api, fields, models


class InvoiceApproval(models.Model):
    """This class creates a model 'invoice.approval' and adds
    required fields"""
    _name = 'invoice.approval'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Invoice Approval'

    name = fields.Char(
        default='Approval Configuration',
        help="Approval configuration.",
    )
    approve_customer_invoice = fields.Boolean(
        string="Approval on Customer Invoice",
        help="Enable this field for adding approvals for customer invoices.",
    )
    invoice_approver_ids = fields.Many2many(
        'res.users',
        'invoice_approval_invoice_user_rel',
        'approval_id',
        'user_id',
        domain=lambda self: [(
            'all_group_ids', 'in',
            self.env.ref('invoice_multi_approval.group_approver').id
        )],
        help='In this field you can add approvers for customer invoices.',
    )
    approve_vendor_bill = fields.Boolean(
        string="Approval on Vendor Bill",
        help="Enable this field for adding approvals for vendor bills.",
    )
    bill_approver_ids = fields.Many2many(
        'res.users',
        'invoice_approval_bill_user_rel',
        'approval_id',
        'user_id',
        domain=lambda self: [(
            'all_group_ids', 'in',
            self.env.ref('invoice_multi_approval.group_approver').id
        )],
        help='In this field you can add approvers for vendor bills.',
    )
    approve_customer_credit = fields.Boolean(
        string='Approval on Customer Refund',
        help="Enable this field for adding approvals for customer credit "
             "notes.",
    )
    cust_credit_approver_ids = fields.Many2many(
        'res.users',
        'invoice_approval_cust_credit_user_rel',
        'approval_id',
        'user_id',
        string='Customer Credit Note Approver',
        domain=lambda self: [(
            'all_group_ids', 'in',
            self.env.ref('invoice_multi_approval.group_approver').id
        )],
        help='In this field you can add approvers for customer credit notes.',
    )
    approve_vendor_credit = fields.Boolean(
        string='Approval on Vendor Refund',
        help="Enable this field for adding approvals for vendor credit notes.",
    )
    vend_credit_approver_ids = fields.Many2many(
        'res.users',
        'invoice_approval_vend_credit_user_rel',
        'approval_id',
        'user_id',
        string='Vendor Credit Note Approver',
        domain=lambda self: [(
            'all_group_ids', 'in',
            self.env.ref('invoice_multi_approval.group_approver').id
        )],
        help='In this field you can add approvers for vendor credit notes.',
    )
