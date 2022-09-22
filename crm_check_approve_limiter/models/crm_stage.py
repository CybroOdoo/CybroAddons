# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Naveen K (odoo@cybrosys.com)
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

"""Module containing Stage-based checklist Models"""
from odoo import models, fields


class StageCheckList(models.Model):
    _inherit = "crm.stage"

    stage_check_list_lines = fields.One2many('stage.check.list',
                                             'stage_id',
                                             string="CheckList")
    pre_checking = fields.Boolean(default=False,
                                  string="No Need for checklist",
                                  help="If checked,moving to next stage doesn't"
                                       "require checklist done.")
    disable_regress = fields.Boolean(default=False,
                                     string="Prohibit Regress to this stage",
                                     help="If checked, It would not be "
                                          "possible to move a lead back to"
                                          " this stage")
