# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import _, api, fields, models


class QueueProcess(models.Model):
    """Model representing a queue process"""
    _name = 'queue.process'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string='Order Reference', readonly=True,
                               copy=False, help='Sequence number',
                               default=lambda self: _('New'))
    counter_id = fields.Many2one('queue.counter', string='Counter',
                                 help='Shows the processed token is from which'
                                      ' department')
    user_id = fields.Many2one('res.users', string="Opened By",
                                help='Who handled the counter',
                                default=lambda self: self.env.uid,
                                readonly=True)
    processed_datetime = fields.Datetime(string='Processed Time', readonly=True,
                                      index=True, default=fields.Datetime.now)
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('done', 'Done')],
                             default='draft', help='State of processed queue')
    department_id = fields.Many2one('department', string='Department',
                                     help='Shows the department')
    customer_name = fields.Char(string='Customer')
    customer_query = fields.Text(string='Customer query')
    feedback = fields.Text(string='Feedback')

    @api.model_create_multi
    def create(self, vals_list):
        """This function creates the reference number"""
        for vals in vals_list:
            if vals.get('reference_no', _('New')) == _('New'):
                vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                    'queue.process') or _('New')
        return super().create(vals_list)

    def _get_report_base_filename(self):
        """Generate filename for reports"""
        self.ensure_one()
        return 'Queue Process - %s' % (self.reference_no)
