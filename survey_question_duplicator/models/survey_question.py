# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import models


class SurveyQuestion(models.Model):
    """To write function for survey question buttons """
    _inherit = 'survey.question'

    def action_add_question(self):
        """Open the duplication wizard for the selected questions."""
        return {
            'name': "Add to Survey",
            'view_mode': 'form',
            'res_model': 'question.duplicate',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': dict(
                self.env.context,
                active_model=self._name,
                active_id=self[:1].id,
                active_ids=self.ids,
            ),
        }
