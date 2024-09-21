# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil @ cybrosys,(odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.fields import Field


class JSON(Field):
    """ Encapsulates an :class:`int`. """
    type = 'json'

    column_type = ('jsonb', 'jsonb')

    def convert_to_column(self, value, record, values=None, validate=True):
        """
            Convert a value to its column form for database storage or usage.
        """

        return str(value) or ""

    def convert_to_record(self, value, record):
        """
            Convert a value to its record form for storing or using in record
            operations.
        """
        return value or {}

    def convert_to_read(self, value, record, use_name_get=True):
        """
        Convert a value to its readable form for displaying or using in read
        operations.
        """
        # Integer values greater than 2^31-1 are not supported in pure XMLRPC,
        # so we have to pass them as floats :-(
        return value

    def _update(self, records, value):
        """
         Update records with a given value.
        """
        # special case, when an integer field is used as inverse for a one2many
        cache = records.env.cache
        for record in records:
            cache.set(record, self, value.id or 0)

    def convert_to_export(self, value, record):
        """
        Convert a value to its exportable form for a specific record.
        """
        if value or value == "":
            return value
        return ''
