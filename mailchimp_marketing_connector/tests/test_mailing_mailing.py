# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from types import SimpleNamespace
from importlib import import_module

from odoo.tests.common import TransactionCase


class TestMailingMailing(TransactionCase):

    def test_onchange_template_id_writes_body(self):
        MailingMailing = import_module(
            'odoo.addons.mailchimp_marketing_connector.models.mailing_mailing'
        ).MailingMailing

        captured = {}

        class FakeRecord:
            template_id = SimpleNamespace(
                share_url='https://example.com/template.png'
            )

            def write(self, vals):
                captured.update(vals)

        MailingMailing._onchange_template_id(FakeRecord())

        self.assertEqual(
            captured['body_arch'],
            '<span/><img src="https://example.com/template.png"/>'
        )

    def test_onchange_template_id_ignores_empty_url(self):
        MailingMailing = import_module(
            'odoo.addons.mailchimp_marketing_connector.models.mailing_mailing'
        ).MailingMailing

        class FakeRecord:
            template_id = SimpleNamespace(share_url='')

            def write(self, vals):
                raise AssertionError('write should not be called')

        MailingMailing._onchange_template_id(FakeRecord())
