# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.sql import column_exists


class ResCompany(models.Model):
    """Inherited Company for the customer sequence configuration.

    The numbers are produced by a dedicated ir.sequence per company, so
    concurrent transactions can never receive the same value.
    """
    _inherit = 'res.company'

    prefix = fields.Char(
        string='Prefix',
        help='Prefix to be added before the customer sequence number, '
             'e.g. CUS will generate CUS-1, CUS-2 ...')
    customer_code = fields.Integer(
        string='Customer code', required=True, default=1,
        help='First number of the customer sequence. It is only used when '
             'the sequence is created; afterwards change "Next code".')
    next_code = fields.Integer(
        string='Next code', compute='_compute_next_code',
        inverse='_inverse_next_code',
        help='Number that will be given to the next customer.')
    customer_sequence_id = fields.Many2one(
        'ir.sequence', string='Customer Sequence', copy=False,
        readonly=True, ondelete='restrict',
        help='Technical sequence used to generate the customer codes.')

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('prefix')
    def _check_prefix_unique(self):
        """Two companies sharing a prefix would generate the same codes."""
        for company in self.filtered('prefix'):
            if self.sudo().search_count([
                    ('id', '!=', company.id),
                    ('prefix', '=', company.prefix)]):
                raise ValidationError(_(
                    "The prefix '%s' is already used by another company. "
                    "Each company needs its own prefix.", company.prefix))

    # ------------------------------------------------------------------
    # Sequence handling
    # ------------------------------------------------------------------
    def _get_sequence_prefix(self):
        self.ensure_one()
        if not self.prefix:
            return ''
        # '%' is a formatting character in ir.sequence prefixes.
        return '%s-' % self.prefix.replace('%', '%%')

    def _create_customer_sequence(self):
        """Create the ir.sequence of this company (row must be locked)."""
        self.ensure_one()
        start = self.customer_code or 1
        # Companies configured with the old hand made counter keep going
        # from where they stopped, so no existing code is generated twice.
        if column_exists(self.env.cr, 'res_company', 'next_code'):
            self.env.cr.execute(
                "SELECT next_code FROM res_company WHERE id = %s",
                (self.id,))
            legacy = self.env.cr.fetchone()
            if legacy and legacy[0]:
                start = legacy[0]
        sequence = self.env['ir.sequence'].sudo().create({
            'name': _('Customer code - %s', self.name),
            'code': 'res.partner.customer.company.%s' % self.id,
            'implementation': 'standard',
            'prefix': self._get_sequence_prefix(),
            'padding': 0,
            'number_next': start,
            'number_increment': 1,
            'company_id': self.id,
        })
        self.sudo().customer_sequence_id = sequence

    def _get_customer_sequence(self):
        """Return the (sudo) customer sequence, creating it if missing."""
        self.ensure_one()
        company = self.sudo()
        if not company.customer_sequence_id:
            # Lock the company row so two transactions cannot both create
            # a sequence for the same company.
            self.env.cr.execute(
                "SELECT 1 FROM res_company WHERE id = %s FOR UPDATE",
                (company.id,))
            company.invalidate_recordset(['customer_sequence_id'])
            if not company.customer_sequence_id:
                company._create_customer_sequence()
        return company.customer_sequence_id

    # ------------------------------------------------------------------
    # Computes / inverses
    # ------------------------------------------------------------------

    def _compute_next_code(self):
        # number_next_actual is a non-stored compute that next_by_id()
        # does not invalidate; read it fresh from the sequence.
        self.sudo().customer_sequence_id.invalidate_recordset(
            ['number_next_actual'])
        for company in self:
            sequence = company.sudo().customer_sequence_id
            company.next_code = (sequence.number_next_actual if sequence
                                 else company.customer_code)

    def _inverse_next_code(self):
        for company in self:
            if company.next_code:
                sequence = company._get_customer_sequence()
                sequence.number_next_actual = company.next_code

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        for company in companies:
            company._get_customer_sequence()
        return companies

    def write(self, vals):
        res = super().write(vals)
        if 'prefix' in vals:
            for company in self:
                sequence = company.sudo().customer_sequence_id
                if sequence:
                    sequence.prefix = company._get_sequence_prefix()
        return res
