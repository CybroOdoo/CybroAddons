# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions K(<https://www.cybrosys.com>)
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
import json
from odoo import models


class Base(models.AbstractModel):
    """To fetch records edited and added into Rollback.Record model."""
    _inherit = 'base'

    def write(self, vals):
        """Creates record when a write function called from any of the base
         models, and store it in rollback model"""
        _excluded_models = {
            'ir.module.module',
            'rollback.record',
            'res.config.settings',
            'ir.config_parameter',
        }
        if self._name not in _excluded_models:
            rollback_models = self.env['rollback.record'].get_models()
            if self._name in rollback_models:
                for rec in self:
                    fields_to_read = [field for field in vals.keys() if field in rec._fields]
                    if fields_to_read:
                        old_values = {}
                        for field in fields_to_read:
                            field_obj = rec._fields[field]
                            if field_obj.type == 'many2one':
                                old_values[field] = rec[field].id or False
                            elif field_obj.type in ('many2many', 'one2many'):
                                old_values[field] = [(6, 0, rec[field].ids)]
                            else:
                                val = rec[field]
                                if field_obj.type in ('date', 'datetime') and val:
                                    old_values[field] = str(val)
                                else:
                                    old_values[field] = val
                        self.env['rollback.record'].create({
                            'res_model': self._name,
                            'record': rec.id,
                            'history': json.dumps(old_values, indent=4, sort_keys=True,
                                                  default=str)
                        })
        return super(Base, self).write(vals)
