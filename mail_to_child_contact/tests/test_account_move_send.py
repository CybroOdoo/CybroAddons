# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bashir Muhammed A (odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountMoveSend(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create parent company partner
        cls.parent_partner = cls.env['res.partner'].create({
            'name': 'Test Parent Company',
            'is_company': True,
            'email': 'parent@example.com',
        })

        # Create child contact partners under parent company (one with mail, one without)
        cls.child_partner_with_mail = cls.env['res.partner'].create({
            'name': 'Child with Mail',
            'parent_id': cls.parent_partner.id,
            'email': 'child_mail@example.com',
        })
        cls.child_partner_no_mail = cls.env['res.partner'].create({
            'name': 'Child without Mail',
            'parent_id': cls.parent_partner.id,
            'email': False,
        })

        # Find or create a sales journal to create an invoice
        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.env.company.id)
        ], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices Test',
                'code': 'TINV',
                'type': 'sale',
                'company_id': cls.env.company.id,
            })

        # Create an account.move invoice
        cls.move = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.parent_partner.id,
            'journal_id': cls.journal.id,
        })

        # Create a mail template
        cls.template = cls.env['mail.template'].create({
            'name': 'Test Invoice Template',
            'model_id': cls.env.ref('account.model_account_move').id,
            'use_default_to': True,
        })

    def test_01_get_default_mail_partner_ids_filtering(self):
        """Test _get_default_mail_partner_ids adds child contacts and filters out those without email by default"""
        # Call the method
        partners = self.env['account.move.send']._get_default_mail_partner_ids(
            self.move,
            self.template,
            'en_US'
        )

        # The parent partner and child partner with email should be returned
        self.assertIn(self.parent_partner, partners)
        self.assertIn(self.child_partner_with_mail, partners)
        # The child partner without email should be filtered out
        self.assertNotIn(self.child_partner_no_mail, partners)

    def test_02_get_default_mail_partner_ids_allow_no_mail(self):
        """Test _get_default_mail_partner_ids with allow_partners_without_mail context does not filter out partners without email"""
        # Call the method with allow_partners_without_mail context
        partners = self.env['account.move.send'].with_context(
            allow_partners_without_mail=True
        )._get_default_mail_partner_ids(
            self.move,
            self.template,
            'en_US'
        )

        # All partners, including the child contact without email, should be returned
        self.assertIn(self.parent_partner, partners)
        self.assertIn(self.child_partner_with_mail, partners)
        self.assertIn(self.child_partner_no_mail, partners)
