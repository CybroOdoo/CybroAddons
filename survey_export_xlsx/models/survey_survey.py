# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Albin P J (odoo@cybrosys.com)
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
################################################################################
from odoo import models


class Survey(models.Model):
    """This will return the wizard"""
    _inherit = 'survey.survey'

    def action_print_xlsx_report(self):
        """Returning the wizard for filtering the report"""
        return {
            'name': 'Survey Answer XLSX Report',
            'res_model': 'survey.xlsx.report',
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_survey_ids': self.ids},
        }
