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
from odoo import api, fields, models


class ResPartner(models.Model):
    """ Inherited Partner for generating unique sequence """
    _inherit = 'res.partner'

    unique_id = fields.Char(
        string='Unique ID', help='Unique code generated for the customer.',
        readonly=True, default='/', copy=False, index=True)
    child_seq = fields.Integer(
        string='Child Sequence', default=0, copy=False,
        help='Internal counter used to generate the sequence for the '
             'related contacts (children) of this partner.')

    sequence_company_id = fields.Many2one(
        'res.company', string='Sequence Company', copy=False,
        readonly=True, ondelete='set null',
        help='Company whose sequence issued the code. Companies without '
             'a prefix all start at 1, so a code is unique per company.')

    # '/' is the placeholder for "no code yet", so it is excluded. The code
    # is unique per issuing company: companies have their own numbering.
    _unique_id_uniq = models.UniqueIndex(
        "(COALESCE(sequence_company_id, 0), unique_id) "
        "WHERE unique_id != '/'",
        "The unique Id of a partner must be unique in its company.")

    def _get_customer_company(self):
        """Company whose sequence is used: the partner's own company,
        falling back to the current one for shared partners."""
        self.ensure_one()
        return (self.company_id or self.env.company).sudo()

    def _next_child_seq(self):
        """Atomically increment and return the child counter. The UPDATE
        takes a row lock, so concurrent children get different numbers."""
        self.ensure_one()
        self.flush_recordset(['child_seq'])
        self.env.cr.execute(
            "UPDATE res_partner SET child_seq = COALESCE(child_seq, 0) + 1 "
            "WHERE id = %s RETURNING child_seq", (self.id,))
        value = self.env.cr.fetchone()[0]
        self.invalidate_recordset(['child_seq'])
        return value

    def _assign_customer_sequence(self):
        """Assign the next sequence value to the partner if it does not
        already have one. Related contacts (children) of an already
        sequenced customer get 'parent_seq/001', top level customers get
        the next number of their company's ir.sequence."""
        self.ensure_one()
        if self.unique_id and self.unique_id != '/':
            return
        parent = self.parent_id
        if parent and parent.unique_id and parent.unique_id != '/':
            self.write({
                'unique_id': '%s/%s' % (
                    parent.unique_id,
                    str(parent._next_child_seq()).zfill(3)),
                'sequence_company_id': parent.sequence_company_id.id,
            })
        else:
            company = self._get_customer_company()
            self.write({
                'unique_id': company._get_customer_sequence().next_by_id(),
                'sequence_company_id': company.id,
            })

    @api.model_create_multi
    def create(self, vals_list):
        """ Super create function for generating sequence.
        - A related contact (has a parent that already has a sequence)
          gets its sequence right away, regardless of customer_rank.
        - A plain contact created with customer_rank == 0 gets nothing;
          it is generated later in write() once it becomes a customer.
        """
        res = super().create(vals_list)
        for record in res:
            if record.unique_id != '/':
                continue
            has_sequenced_parent = record.parent_id and \
                record.parent_id.unique_id and \
                record.parent_id.unique_id != '/'
            if has_sequenced_parent or record.customer_rank > 0:
                record._assign_customer_sequence()
        return res

    def write(self, vals):
        """ Generate the sequence the moment a plain contact is turned
        into a customer by increasing its customer_rank. """
        res = super().write(vals)
        if 'customer_rank' in vals:
            for record in self:
                if record.customer_rank > 0 and record.unique_id == '/':
                    record._assign_customer_sequence()
        return res
