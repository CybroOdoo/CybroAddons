# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Aleena K(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestOrgContacts(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '9876543210',
        })
        cls.contact = cls.env['org.contacts'].create({
            'contact_id': cls.partner.id,
        })

    def test_contact_creation(self):
        """Test contact creation"""
        self.assertRecordValues(self.contact, [{
            'contact_id': self.partner.id,
        }])

    def test_contact_partner_relation(self):
        """Test partner relation"""
        self.assertRecordValues(self.contact.contact_id, [{
            'name': 'John Doe',
            'email': 'john@example.com',
        }])

    def test_contact_delete(self):
        """Test contact deletion"""
        contact_id = self.contact.id
        self.contact.unlink()
        deleted_contact = self.env['org.contacts'].browse(
            contact_id
        )
        self.assertFalse(
            deleted_contact.exists(),
            "Contact was not deleted properly"
        )
