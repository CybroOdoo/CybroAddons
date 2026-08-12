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
from datetime import datetime
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import re


class TokenToken(models.Model):
    """Model for managing queue tokens and related operations."""
    _name = 'token.token'
    _description = 'Token'
    _rec_name = 'reference_no'

    reference_no = fields.Char(
        string='Order Reference',
        readonly=True,
        copy=False,
        default=lambda self: _('New'),
        help='Sequence number'
    )
    token = fields.Char(
        string="Token",
        readonly=True,
        copy=False,
        default=lambda self: self._generate_token(),
        help="Generated token number"
    )
    customer_name = fields.Char(string='Name')
    department_id = fields.Many2one('department', string="Department")
    mobile = fields.Char(string="Contact Number")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('recall', 'Recall'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], default='draft')
    token_datetime = fields.Datetime(
        string='Opened Time',
        readonly=True,
        index=True,
        default=fields.Datetime.now
    )
    counter_id = fields.Many2one('queue.counter', string='Counter')

    @api.constrains('mobile')
    def _check_mobile(self):
        pattern = r'^\+?[0-9()\-\s]{7,20}$'

        for rec in self:
            if rec.mobile and not re.fullmatch(pattern, rec.mobile):
                raise ValidationError(
                    "Phone number cannot contain alphabets."
                )

    @api.model
    def _generate_token(self):
        """Generate a unique token using sequence."""
        return self.env['ir.sequence'].next_by_code('token.token') or _('New')

    @api.model_create_multi
    def create(self, vals_list):
        """Assign sequence-based reference number during record creation."""
        for vals in vals_list:
            if vals.get('reference_no', _('New')) == _('New'):
                vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                    'token.token'
                ) or _('New')
        return super().create(vals_list)

    def _get_report_base_filename(self):
        """Return the report filename for the token."""
        self.ensure_one()
        return f'Token - {self.reference_no}'

    @api.model
    def get_tokens(self, from_date=None, to_date=None):
        """Return token statistics filtered by date range."""
        from_date = fields.Date.to_date(from_date) if from_date else fields.Date.today()
        to_date = fields.Date.to_date(to_date) if to_date else from_date
        start_dt = datetime.combine(from_date, datetime.min.time())
        end_dt = datetime.combine(to_date, datetime.max.time())
        domain = [
            ('token_datetime', '>=', start_dt),
            ('token_datetime', '<=', end_dt)
        ]
        tokens = self.search(domain)
        return {
            'total_queue_count': len(tokens),
            'total_queue_served': len(tokens.filtered(lambda t: t.state == 'done')),
            'total_queue_left': len(tokens.filtered(lambda t: t.state == 'draft')),
        }

    @api.model
    def pie_function(self, from_date=None, to_date=None):
        """Return token counts grouped by state for chart visualization."""
        domain_sql = ""
        params = []
        if from_date and to_date:
            from_date = fields.Date.to_date(from_date)
            to_date = fields.Date.to_date(to_date)
            start_dt = datetime.combine(from_date, datetime.min.time())
            end_dt = datetime.combine(to_date, datetime.max.time())
            domain_sql = "WHERE token_datetime >= %s AND token_datetime <= %s"
            params = [start_dt, end_dt]
        query = f"""
            SELECT COUNT(id) AS count, state
            FROM {self._table}
            {domain_sql}
            GROUP BY state
        """
        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        return {
            'name': [r['state'] for r in result],
            'count': [r['count'] for r in result]
        }
    
    @api.model
    def get_table_data(self, from_date=None, to_date=None):
        """Return department-wise aggregated token data for reporting."""
        where_clause = ""
        params = []
        if from_date and to_date:
            from_date = fields.Date.to_date(from_date)
            to_date = fields.Date.to_date(to_date)
            start_dt = datetime.combine(from_date, datetime.min.time())
            end_dt = datetime.combine(to_date, datetime.max.time())
            where_clause = "WHERE t.token_datetime >= %s AND t.token_datetime <= %s"
            params = [start_dt, end_dt]
        query = f"""
            SELECT
                d.name AS department,
                COUNT(t.id) AS count,
                SUM(CASE WHEN t.state = 'done' THEN 1 ELSE 0 END) AS done,
                SUM(CASE WHEN t.state = 'draft' THEN 1 ELSE 0 END) AS draft,
                SUM(CASE WHEN t.state = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
            FROM {self._table} t
            JOIN department d ON d.id = t.department_id
            {where_clause}
            GROUP BY d.name
        """
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()
