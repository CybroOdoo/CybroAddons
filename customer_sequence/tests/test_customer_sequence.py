# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestCustomerSequence(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.Partner = self.env['res.partner']
        self.Company = self.env['res.company']
        # No prefix, and make sure the company has its sequence, starting
        # at 1000 (works whether or not the sequence already existed).
        self.company.write({'prefix': False})
        self.company._get_customer_sequence()
        self.company.next_code = 1000

    def _next_code(self, company=None):
        """next_code is a non stored compute: drop its cache so it is
        recomputed. The compute itself refreshes the sequence value."""
        company = company or self.company
        company.invalidate_recordset(['next_code'])
        return company.next_code

    # ------------------------------------------------------------------
    # Basic customer numbering
    # ------------------------------------------------------------------
    def test_01_customer_sequence_initial(self):
        """First customer gets the starting code."""
        partner = self.Partner.create({
            'name': 'Test Customer 1',
            'customer_rank': 1,
        })

        self.assertEqual(partner.unique_id, '1000',
                         "Unique ID should be 1000")
        self.assertEqual(partner.name, 'Test Customer 1',
                         "Name should remain unchanged")
        self.assertEqual(self._next_code(), 1001,
                         "Next code should be incremented to 1001")

    def test_02_customer_sequence_next_code(self):
        """Changing 'Next code' on the company changes the next number."""
        self.company.next_code = 2000
        self.assertEqual(self._next_code(), 2000)

        partner = self.Partner.create({
            'name': 'Test Customer 2',
            'customer_rank': 1,
        })

        self.assertEqual(partner.unique_id, '2000',
                         "Unique ID should be 2000")
        self.assertEqual(partner.name, 'Test Customer 2',
                         "Name should remain unchanged")
        self.assertEqual(self._next_code(), 2001,
                         "Next code should be incremented to 2001")

    def test_03_non_customer_sequence(self):
        """Sequence is not generated for non-customers."""
        partner = self.Partner.create({
            'name': 'Test Vendor',
            'customer_rank': 0,
            'supplier_rank': 1,
        })

        self.assertEqual(partner.unique_id, '/',
                         "Unique ID should be '/' for non-customers")
        self.assertEqual(partner.name, 'Test Vendor',
                         "Name should remain unchanged")
        self.assertEqual(self._next_code(), 1000,
                         "Next code should not be touched")

    def test_04_customer_sequence_multi(self):
        """Sequence generation when multiple partners are created at once."""
        partners = self.Partner.create([
            {'name': 'Test Multi 1', 'customer_rank': 1},
            {'name': 'Test Multi 2', 'customer_rank': 1},
        ])

        self.assertEqual(len(partners), 2)
        self.assertEqual(partners[0].unique_id, '1000')
        self.assertEqual(partners[1].unique_id, '1001')
        self.assertEqual(self._next_code(), 1002)

    def test_05_customer_sequence_with_prefix(self):
        """Sequence includes the company prefix when it is set."""
        self.company.write({'prefix': 'CUS'})
        partner = self.Partner.create({
            'name': 'Test Prefix Customer',
            'customer_rank': 1,
        })

        self.assertEqual(partner.unique_id, 'CUS-1000')
        self.assertEqual(self._next_code(), 1001)

    def test_06_sequence_on_customer_rank_write(self):
        """Sequence is generated when a contact becomes a customer."""
        partner = self.Partner.create({
            'name': 'Test Later Customer',
            'customer_rank': 0,
        })
        self.assertEqual(partner.unique_id, '/')

        partner.write({'customer_rank': 1})

        self.assertEqual(partner.unique_id, '1000')
        self.assertEqual(self._next_code(), 1001)

    def test_07_sequence_not_regenerated(self):
        """An existing sequence is kept when the partner is updated."""
        partner = self.Partner.create({
            'name': 'Test Existing Customer',
            'customer_rank': 1,
        })
        partner.write({'customer_rank': 2})

        self.assertEqual(partner.unique_id, '1000')
        self.assertEqual(self._next_code(), 1001,
                         "Counter should not advance again")

    # ------------------------------------------------------------------
    # Related contacts (children)
    # ------------------------------------------------------------------
    def test_08_child_contact_sequence(self):
        """Child contacts of a sequenced customer get parent/001, /002."""
        parent = self.Partner.create({
            'name': 'Test Parent',
            'customer_rank': 1,
        })
        child_1 = self.Partner.create({
            'name': 'Test Child 1',
            'parent_id': parent.id,
        })
        child_2 = self.Partner.create({
            'name': 'Test Child 2',
            'parent_id': parent.id,
        })

        self.assertEqual(parent.unique_id, '1000')
        self.assertEqual(child_1.unique_id, '1000/001')
        self.assertEqual(child_2.unique_id, '1000/002')
        self.assertEqual(parent.child_seq, 2)
        self.assertEqual(self._next_code(), 1001,
                         "Children should not consume company codes")

    def test_09_child_contact_with_prefix(self):
        """The child code is built on the prefixed parent code."""
        self.company.write({'prefix': 'CUS'})
        parent = self.Partner.create({
            'name': 'Test Prefix Parent',
            'customer_rank': 1,
        })
        child = self.Partner.create({
            'name': 'Test Prefix Child',
            'parent_id': parent.id,
        })

        self.assertEqual(parent.unique_id, 'CUS-1000')
        self.assertEqual(child.unique_id, 'CUS-1000/001')

    def test_10_child_of_non_customer_gets_nothing(self):
        """A child of a parent without a sequence stays '/'."""
        parent = self.Partner.create({
            'name': 'Test Plain Parent',
            'customer_rank': 0,
        })
        child = self.Partner.create({
            'name': 'Test Plain Child',
            'parent_id': parent.id,
        })

        self.assertEqual(parent.unique_id, '/')
        self.assertEqual(child.unique_id, '/')
        self.assertEqual(self._next_code(), 1000)

    # ------------------------------------------------------------------
    # Company prefix / sequence handling
    # ------------------------------------------------------------------
    def test_11_prefix_change_applies_to_next_codes(self):
        """Changing the prefix keeps the counter and updates the format."""
        first = self.Partner.create({
            'name': 'Before Prefix', 'customer_rank': 1})
        self.company.write({'prefix': 'ABC'})
        second = self.Partner.create({
            'name': 'After Prefix', 'customer_rank': 1})

        self.assertEqual(first.unique_id, '1000')
        self.assertEqual(second.unique_id, 'ABC-1001',
                         "Old codes stay, new ones use the new prefix")

        self.company.write({'prefix': False})
        third = self.Partner.create({
            'name': 'Prefix Removed', 'customer_rank': 1})
        self.assertEqual(third.unique_id, '1002')

    def test_12_prefix_with_percent_sign(self):
        """A '%' in the prefix must not break the sequence formatting."""
        self.company.write({'prefix': 'A%B'})
        partner = self.Partner.create({
            'name': 'Percent Customer', 'customer_rank': 1})

        self.assertEqual(partner.unique_id, 'A%B-1000')

    def test_13_duplicate_prefix_not_allowed(self):
        """Two companies cannot share the same prefix."""
        self.company.write({'prefix': 'DUP'})
        with self.assertRaises(ValidationError):
            self.Company.create({'name': 'Dup Company', 'prefix': 'DUP'})

    def test_14_sequence_created_lazily(self):
        """A company without sequence gets one from 'Customer code'."""
        old_sequence = self.company.customer_sequence_id
        self.company.sudo().customer_sequence_id = False
        old_sequence.sudo().unlink()
        self.company.write({'customer_code': 3000})
        self.assertEqual(self._next_code(), 3000,
                         "Without a sequence 'Next code' shows the start")

        partner = self.Partner.create({
            'name': 'Lazy Sequence Customer', 'customer_rank': 1})

        self.assertTrue(self.company.customer_sequence_id)
        self.assertEqual(partner.unique_id, '3000')
        self.assertEqual(self._next_code(), 3001)

    def test_15_new_company_has_own_sequence(self):
        """A new company gets its own sequence and numbering."""
        company = self.Company.create({
            'name': 'Second Company',
            'prefix': 'SEC',
            'customer_code': 500,
        })

        self.assertTrue(company.customer_sequence_id)
        self.assertNotEqual(company.customer_sequence_id,
                            self.company.customer_sequence_id)
        self.assertEqual(self._next_code(company), 500)

        partner = self.Partner.with_company(company).create({
            'name': 'Second Company Customer',
            'customer_rank': 1,
            'company_id': company.id,
        })
        self.assertEqual(partner.unique_id, 'SEC-500')
        self.assertEqual(self._next_code(company), 501)
        self.assertEqual(self._next_code(), 1000,
                         "The other company counter is untouched")

    def test_16_partner_company_decides_sequence(self):
        """The sequence used is the one of the partner's own company."""
        company = self.Company.create({
            'name': 'Third Company', 'prefix': 'THI'})
        partner = self.Partner.create({
            'name': 'Cross Company Customer',
            'customer_rank': 1,
            'company_id': company.id,
        })

        self.assertEqual(partner.unique_id, 'THI-1')
        self.assertEqual(self._next_code(), 1000,
                         "Current company counter must not move")

    # ------------------------------------------------------------------
    # Partner field behaviour
    # ------------------------------------------------------------------
    def test_17_fields_not_copied(self):
        """Duplicating a customer must not copy its codes."""
        partner = self.Partner.create({
            'name': 'Copy Source', 'customer_rank': 1})
        copied_vals = partner.copy_data()[0]

        self.assertNotIn('unique_id', copied_vals)
        self.assertNotIn('child_seq', copied_vals)
        self.assertNotIn('sequence_company_id', copied_vals)

    def test_18_unique_id_is_unique(self):
        """The same code cannot be given to two partners of the same
        company, '/' can repeat."""
        first = self.Partner.create({
            'name': 'Unique 1', 'customer_rank': 1})
        second = self.Partner.create({'name': 'Plain 1'})
        third = self.Partner.create({'name': 'Plain 2'})
        self.assertEqual(second.unique_id, '/')
        self.assertEqual(third.unique_id, '/')

        with self.assertRaises(IntegrityError), \
                mute_logger('odoo.sql_db'), self.cr.savepoint():
            second.write({
                'unique_id': first.unique_id,
                'sequence_company_id': first.sequence_company_id.id,
            })
            second.flush_recordset()

    # ------------------------------------------------------------------
    # next_code freshness / sequence backing
    # ------------------------------------------------------------------
    def test_19_next_code_not_stale_after_create(self):
        """next_by_id() does not invalidate number_next_actual: the
        compute must still show the new value once it is recomputed."""
        self.assertEqual(self.company.next_code, 1000)
        self.Partner.create({'name': 'Stale Check', 'customer_rank': 1})

        # Only next_code is dropped; number_next_actual may still be
        # cached and the compute has to refresh it on its own.
        self.company.invalidate_recordset(['next_code'])
        self.assertEqual(self.company.next_code, 1001)

    def test_20_codes_come_from_ir_sequence(self):
        """Codes are produced by the company's ir.sequence."""
        sequence = self.company.customer_sequence_id
        self.assertEqual(sequence._name, 'ir.sequence')
        self.assertEqual(sequence.company_id, self.company)

        partner = self.Partner.create({
            'name': 'Sequence Backed', 'customer_rank': 1})
        self.assertEqual(partner.unique_id, '1000')
        sequence.invalidate_recordset(['number_next_actual'])
        self.assertEqual(sequence.number_next_actual, 1001)

    def test_21_shared_partner_uses_current_company(self):
        """A partner without a company uses the current company."""
        partner = self.Partner.create({
            'name': 'Shared Customer',
            'customer_rank': 1,
            'company_id': False,
        })
        self.assertEqual(partner.unique_id, '1000')
        self.assertEqual(partner.sequence_company_id, self.company)
        self.assertEqual(self._next_code(), 1001)

    def test_22_customer_code_default(self):
        """The required start value has a default."""
        company = self.Company.create({'name': 'Default Code Company'})
        self.assertEqual(company.customer_code, 1)
        self.assertEqual(self._next_code(company), 1)

    # ------------------------------------------------------------------
    # Several companies without prefix
    # ------------------------------------------------------------------
    def test_23_same_code_allowed_in_different_companies(self):
        """Companies without prefix all start at 1: the same code may
        exist once per company (this broke other modules' tests)."""
        company_a = self.Company.create({'name': 'No Prefix A'})
        company_b = self.Company.create({'name': 'No Prefix B'})
        partner_a = self.Partner.create({
            'name': 'Customer A', 'customer_rank': 1,
            'company_id': company_a.id})
        partner_b = self.Partner.create({
            'name': 'Customer B', 'customer_rank': 1,
            'company_id': company_b.id})

        self.assertEqual(partner_a.unique_id, '1')
        self.assertEqual(partner_b.unique_id, '1')
        self.assertEqual(partner_a.sequence_company_id, company_a)
        self.assertEqual(partner_b.sequence_company_id, company_b)

    def test_24_child_keeps_parent_sequence_company(self):
        """A child code is scoped to the company of its parent's code."""
        company = self.Company.create({'name': 'Child Scope Company'})
        parent = self.Partner.create({
            'name': 'Scoped Parent', 'customer_rank': 1,
            'company_id': company.id})
        child = self.Partner.create({
            'name': 'Scoped Child', 'parent_id': parent.id})

        self.assertEqual(child.unique_id, '1/001')
        self.assertEqual(child.sequence_company_id, company)
