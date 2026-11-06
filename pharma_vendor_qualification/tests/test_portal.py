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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import HttpCase, tagged

from .common import PharmaVendorCommon


@tagged('post_install', '-at_install')
class TestPortal(PharmaVendorCommon, HttpCase):
    """The vendor answers the questionnaire through the token link."""

    def setUp(self):
        """A qualification whose questionnaire was sent to the vendor."""
        super().setUp()
        self.qualification = self.create_qualification()
        self.qualification.action_send_questionnaire()
        self.url = '/pharma/vendor/questionnaire/%d' % self.qualification.id

    def answers(self, number='12'):
        """Form data answering every question."""
        data = {'access_token': self.qualification.access_token}
        for response in self.qualification.response_ids:
            data.update({
                'yes_no': {'answer_yes_no_%d' % response.id: 'yes'},
                'text': {'answer_text_%d' % response.id: 'CAPA within 30 days.'},
                'number': {'answer_number_%d' % response.id: number},
                'file': {},
            }[response.answer_type])
        return data

    def files(self):
        """The uploaded certificate for the file question."""
        response = self.qualification.response_ids.filtered(lambda r: r.answer_type == 'file')
        return {'answer_file_%d' % response.id: ('gmp.pdf', b'%PDF-1.4 certificate', 'application/pdf')}

    def test_token_required(self):
        """The form opens only with the right token."""
        page = self.url_open(self.url + '?access_token=%s' % self.qualification.access_token)
        self.assertIn('Batches per month?', page.text)
        self.assertNotIn('Batches per month?', self.url_open(self.url + '?access_token=wrong').text)
        self.assertNotIn('Batches per month?', self.url_open(self.url).text)
        denied = self.url_open(self.url + '/submit', data={'access_token': 'wrong'})
        self.assertNotIn('Batches per month?', denied.text)

    def test_submit(self):
        """A complete submission stores the answers and moves to Documents Received."""
        self.url_open(self.url + '/submit', data=self.answers(), files=self.files())
        self.qualification.invalidate_recordset()
        responses = {r.answer_type: r for r in self.qualification.response_ids}
        self.assertEqual(self.qualification.status, 'documents_received')
        self.assertTrue(self.qualification.submission_date)
        self.assertEqual(responses['yes_no'].answer_yes_no, 'yes')
        self.assertEqual(responses['number'].answer_number, 12.0)
        self.assertEqual(responses['file'].answer_file_filename, 'gmp.pdf')

    def test_closed_after_submission(self):
        """Once submitted, the link shows the questionnaire is closed and refuses new answers."""
        self.url_open(self.url + '/submit', data=self.answers(), files=self.files())
        page = self.url_open(self.url + '?access_token=%s' % self.qualification.access_token)
        self.assertIn('Questionnaire Closed', page.text)
        self.assertNotIn('Batches per month?', page.text)
        page = self.url_open(self.url + '/submit', data=self.answers(number='99'), files=self.files())
        self.assertIn('Questionnaire Closed', page.text)
        self.qualification.invalidate_recordset()
        number = self.qualification.response_ids.filtered(lambda r: r.answer_type == 'number')
        self.assertEqual(number.answer_number, 12.0)

    def test_submit_errors(self):
        """A missing file or a non-numeric answer is refused and nothing is saved."""
        page = self.url_open(self.url + '/submit', data=self.answers())
        self.assertIn('A file is required for', page.text)
        page = self.url_open(self.url + '/submit', data=self.answers(number='a dozen'), files=self.files())
        self.assertIn('Enter a number for', page.text)
        self.qualification.invalidate_recordset()
        self.assertEqual(self.qualification.status, 'questionnaire_sent')
        self.assertFalse(self.qualification.response_ids.filtered(lambda r: r.answer_type == 'yes_no').answer_yes_no)
