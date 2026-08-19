# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anupriya Ashok (<https://www.cybrosys.com>)
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
from odoo import models

class ProjectProject(models.Model):
    _inherit = 'project.project'

    def fields_get(self, allfields=None, attributes=None):
        """
         Extension of the `project.project` model to ensure only valid
         model fields are returned and read."""
        res = super().fields_get(allfields, attributes)
        valid_fields = set(self._fields.keys())
        return {k: v for k, v in res.items() if k in valid_fields}

    def read(self, fields=None, load=None):
        """
             Override of `read` to filter out invalid field names before
             performing the read operation."""
        if fields:
            valid = set(self._fields.keys())
            fields = [f for f in fields if f in valid]
        return super().read(fields=fields, load=load)
