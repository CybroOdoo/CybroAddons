# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
        for rec in self:
            if self._name != 'ir.module.module':
                self.env['rollback.record'].create({
                    'res_model': self._name,
                    'record': rec.id,
                    'history': json.dumps(vals, indent=4, sort_keys=True,
                                          default=str)
                })
        return super(Base, self).write(vals)
