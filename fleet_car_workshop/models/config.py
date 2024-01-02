# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: ASWATHI C (<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.tools.translate import _
from odoo import fields, models, api

from odoo import fields, models


class WorkshopSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_journal_type = fields.Many2one('account.journal', string="Car Workshop Journal",
                                           config_parameter='fleet_car_workshop.invoice_journal_type')


class WorksheetTags(models.Model):
    _name = "worksheet.tags"
    _description = "Tags of vehicles's tasks, issues..."

    name = fields.Char('Name', required=True)
    color = fields.Integer('Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]


class WorksheetStages(models.Model):
    _name = 'worksheet.stages'
    _description = 'worksheet Stage'
    _order = 'sequence'

    def _get_default_vehicle_ids(self):
        default_vehicle_id = self.env.context.get('default_vehicle_id')
        return [default_vehicle_id] if default_vehicle_id else None

    name = fields.Char(string='Stage Name', required=True)
    description = fields.Text(string='Description', translate=True)
    sequence = fields.Integer(string='Sequence')
    vehicle_ids = fields.Many2many('car.car', 'worksheet_type_rel', 'type_id', 'vehicle_id', string='Vechicles',
                                   default=_get_default_vehicle_ids)
    fold = fields.Boolean('Folded in Tasks Pipeline',
                          help='This stage is folded in the kanban view when '
                               'there are no records in that stage to display.')
