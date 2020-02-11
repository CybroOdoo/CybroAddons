# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nilmar Shereef(<https://www.cybrosys.com>)
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


class WorkshopSetting(models.Model):
    _name = "workshop.config.setting"

    invoice_journal_type = fields.Many2one('account.journal', string="Car Workshop Journal")

    @api.multi
    def execute(self):
        return self.env['ir.values'].sudo().set_default(
            'workshop.config.setting', 'invoice_journal_type', self.invoice_journal_type.id)

    def cancel(self, cr, uid, ids, context=None):
        act_window = self.pool['ir.actions.act_window']
        action_ids = act_window.search(cr, uid, [('res_model', '=', self._name)])
        if action_ids:
            return act_window.read(cr, uid, action_ids[0], [], context=context)
        return {}


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

    name = fields.Char(string='Stage Name', required=True)
    description = fields.Text(string='Description', translate=True)
    sequence = fields.Integer(string='Sequence')
    vehicle_ids = fields.Many2many('car.car', 'worksheet_type_rel', 'type_id', 'vehicle_id', string='Vechicles')
    fold = fields.Boolean('Folded in Tasks Pipeline',
                          help='This stage is folded in the kanban view when '
                               'there are no records in that stage to display.')

    def _get_default_vehicle_ids(self, cr, uid, ctx=None):
        if ctx is None:
            ctx = {}
        default_vehicle_id = ctx.get('default_vehicle_id')
        return [default_vehicle_id] if default_vehicle_id else None

    _defaults = {
        'sequence': 1,
        'vehicle_ids': _get_default_vehicle_ids,
    }
    _order = 'sequence'

