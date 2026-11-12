# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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

from odoo import models, fields, api


class PosPrintTemplate(models.Model):
    """
     POS Print Template model.

    This model allows defining custom POS receipt templates that are uploaded
    as QWeb XML files. Each template can dynamically create its own QWeb view
    and corresponding PDF report action for POS orders.
    """
    _name = "pos.print.template"
    _description = "POS Print Template"

    name = fields.Char(required=True)
    report_id = fields.Many2one(
        "ir.actions.report",
        string="QWeb Report",
        required=False,
        readonly=True
    )
    active = fields.Boolean(default=True)
    is_default = fields.Boolean(default=False)

    @api.constrains('is_default')
    def _check_one_default(self):
        for template in self:
            if not template.is_default:
                continue
            other_defaults = self.search([
                ('is_default', '=', True), ('id', '!=', template.id),
            ])
            if other_defaults:
                other_defaults.write({'is_default': False})
