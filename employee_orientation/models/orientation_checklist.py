# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha @cybrosys(odoo@cybrosys.com)
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
#############################################################################

from odoo import models, fields, _


class OrientationChecklist(models.Model):
    _name = 'orientation.checklist'
    _description = "Checklist"
    _rec_name = 'checklist_name'
    _inherit = 'mail.thread'

    checklist_name = fields.Char(string='Name', required=True)
    checklist_department = fields.Many2one('hr.department', string='Department', required=True)
    active = fields.Boolean(string='Active', default=True,
                            help="Set active to false to hide the Orientation Checklist without removing it.")
    checklist_line_id = fields.Many2many('checklist.line', 'checklist_line_rel', String="Checklist")







