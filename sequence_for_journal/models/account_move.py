# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohamed Muzammil VP(odoo@cybrosys.com)
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
###############################################################################
from odoo import models


class AccountMove(models.Model):
    """inherit account.move to add methods"""
    _inherit = 'account.move'

    def _get_starting_sequence(self):
        """Overriding the methode, this methode get the initial sequence of a
        journal"""
        self.ensure_one()
        if self.journal_id.type in ['sale', 'bank', 'cash'] and \
                self.journal_id.sequence_id.suffix:
            starting_sequence = "%s/%s/%s%s" % (
                self.journal_id.sequence_id.prefix,
                self.date.year,
                self.journal_id.step_size,
                self.journal_id.sequence_id.suffix)
        elif self.journal_id.type in ['sale', 'bank', 'cash']:
            starting_sequence = "%s/%s/000%d" % (
                self.journal_id.code,
                self.date.year,
                self.journal_id.step_size)
        elif self.journal_id.type in ['purchase', 'general'] and \
                self.journal_id.sequence_id.suffix:
            starting_sequence = "%s/%s/%s%s" % (
                self.journal_id.sequence_id.prefix, self.date.year,
                self.journal_id.step_size,
                self.journal_id.sequence_id.suffix)
        else:
            starting_sequence = "%s/%s/%s000" % (
                self.journal_id.code, self.date.year,
                self.journal_id.default_step_size)
        if self.journal_id.refund_sequence and self.move_type in (
                'out_refund', 'in_refund'):
            starting_sequence = "R" + starting_sequence
        if self.journal_id.payment_sequence and self.payment_id or \
                self._context.get('is_payment'):
            starting_sequence = "P" + starting_sequence
        return starting_sequence

    def _set_next_sequence(self):
        """Overriding, to get the next sequence number"""
        self.ensure_one()
        last_sequence = self._get_last_sequence()
        new = not last_sequence
        if new:
            last_sequence = self._get_last_sequence(relaxed=True) or \
                            self._get_starting_sequence()

        format, format_values = self._get_sequence_format_param(last_sequence)
        if new:
            format_values['seq'] = 0
        if self.journal_id.sequence_id.number_increment > 0:
            interpolated_prefix, interpolated_suffix = \
                self.journal_id.sequence_id._get_prefix_suffix()
            format_values['seq'] = format_values['seq'] + self.journal_id.\
                sequence_id.number_increment
            format_values['prefix1'] = interpolated_prefix + "/"
            if self.journal_id.sequence_id.suffix:
                format_values[
                    'suffix'] = "/" + interpolated_suffix
            else:
                format_values['suffix'] = ""
        else:
            format_values['seq'] = format_values['seq'] + \
                                   self.journal_id.default_step_size
        self[self._sequence_field] = format.format(**format_values)
        self._compute_split_sequence()
