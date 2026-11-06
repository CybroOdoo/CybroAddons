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
from odoo.addons.pharmaceutical_base.tests.common import PharmaTestCommon


class PharmaVendorCommon(PharmaTestCommon):
    """A vendor, a questionnaire template and helpers for qualifications."""

    @classmethod
    def setUpClass(cls):
        """Give the role users purchase rights and create the vendor and template."""
        super().setUpClass()
        purchase_user = cls.env.ref('purchase.group_purchase_user')
        (cls.operator | cls.qa_user).group_ids = [(4, purchase_user.id)]
        cls.product_tmpl.product_type_pharma = 'api'
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Acme Pharma Supplies', 'email': 'qa@acme.example', 'supplier_rank': 1,
        })
        cls.template = cls.env['pharma.questionnaire.template'].create({
            'name': 'GMP Supplier Questionnaire',
            'question_ids': [
                (0, 0, {'section': 'Quality', 'question_text': 'Do you hold a GMP certificate?', 'answer_type': 'yes_no'}),
                (0, 0, {'section': 'Quality', 'question_text': 'Describe your deviation process.', 'answer_type': 'text'}),
                (0, 0, {'section': 'Capacity', 'question_text': 'Batches per month?', 'answer_type': 'number', 'sequence': 20}),
                (0, 0, {'section': 'Documents', 'question_text': 'Upload your GMP certificate.', 'answer_type': 'file', 'sequence': 30}),
            ],
        })

    def create_qualification(self, total_score=100.0):
        """A draft qualification of the vendor for the API, raised by the operator."""
        return self.env['pharma.vendor.qualification'].with_user(self.operator).create({
            'vendor_id': self.vendor.id,
            'product_ids': [(6, 0, self.product_tmpl.ids)],
            'total_score': total_score,
            'template_id': self.template.id,
        })

    def scheduled_qualification(self):
        """A qualification whose audit is scheduled for today."""
        qualification = self.create_qualification()
        qualification.action_send_questionnaire()
        qualification.action_receive_documents()
        qualification.audit_date = self.env.cr.now().date()
        qualification.action_schedule_audit()
        return qualification.with_user(self.env.user)

    def approved_qualification(self, score=90.0):
        """A qualification QA approved with ``score``."""
        qualification = self.scheduled_qualification()
        qualification.with_user(self.qa_user).audit_score = score
        qualification.with_user(self.qa_user).action_approve()
        return qualification
