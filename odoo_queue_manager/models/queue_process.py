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


class QueueProcess(models.Model):
    """Model representing a queue process"""
    _name = 'queue.process'
    _description = 'Queue Process'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string='Order Reference', readonly=True,
                               copy=False, help='Sequence number',
                               default=lambda self: self.env._('New'))
    counter_id = fields.Many2one(
        'queue.counter',
        help="Service counter where the token was processed"
    )
    user_id = fields.Many2one(
        'res.users',
        string="Opened By",
        help="User who handled the counter service",
        default=lambda self: self.env.uid,
        readonly=True
    )
    processed_datetime = fields.Datetime(
        string='Processed Time',
        readonly=True,
        index=True,
        default=fields.Datetime.now
    )
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('done', 'Done')],
        default='draft',
        help='State of processed queue'
    )
    department_id = fields.Many2one(
        'queue.department',
        help="Department associated with the token"
    )
    customer_name = fields.Char(string='Customer')
    customer_query = fields.Text()
    feedback = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        """This function creates the reference number"""
        for vals in vals_list:
            if vals.get('reference_no', self.env._('New')) == self.env._('New'):
                vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                    'queue.process') or self.env._('New')
        return super().create(vals_list)

    def _get_report_base_filename(self):
        """Generate filename for reports"""
        self.ensure_one()
        return 'Queue Process - %s' % (self.reference_no)
