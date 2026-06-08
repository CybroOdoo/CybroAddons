# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys(odoo@cybrosys.com)
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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSurveySurvey(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.survey = cls.env['survey.survey'].create({
            'title': 'Test Customer Feedback Survey',
        })

    def test_01_action_whatsapp_send(self):
        """Test action_whatsapp_send returns correct act_window action."""
        res = self.survey.action_whatsapp_send()
        self.assertEqual(res['name'], "Whatsapp Share")
        self.assertEqual(res['type'], 'ir.actions.act_window')
        self.assertEqual(res['view_mode'], 'form')
        self.assertEqual(res['res_model'], 'survey.whatsapp')
        self.assertEqual(res['target'], 'new')
        self.assertEqual(res['context']['default_survey_id'], self.survey.id)
