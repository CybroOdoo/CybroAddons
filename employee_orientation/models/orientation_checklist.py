# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen @cybrosys(odoo@cybrosys.com)
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
from odoo import models, fields


class OrientationChecklist(models.Model):
    """This class creates a model 'orientation.checklist' and added fields"""
    _name = 'orientation.checklist'
    _description = "Checklist"
    _rec_name = 'checklist_name'
    _inherit = 'mail.thread'

    checklist_name = fields.Char(string='Name', required=True,
                                 help="Give the checklist name.")
    checklist_department_id = fields.Many2one('hr.department',
                                              string='Department',
                                              required=True,
                                              help="Give the corresponding"
                                                   "department.")
    active = fields.Boolean(string='Active', default=True,
                            help="Set active to false to hide the Orientation "
                                 "Checklist without removing it.")
    checklist_line_ids = fields.Many2many('checklist.line',
                                          'checklist_line_rel',
                                          help="Specify all the checklists.")
