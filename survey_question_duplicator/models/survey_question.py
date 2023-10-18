# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
################################################################################
from odoo import models


class SurveyQuestion(models.Model):
    """Inherited survey question to include the add_to_survey action"""
    _inherit = 'survey.question'

    def action_add_question(self):
        """Method for opening the wizard for selecting the surveys"""
        return {
            'name': "Add To Survey",
            'view_mode': 'form',
            'res_model': 'survey.selector',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'active_ids': self.ids
            }
        }
