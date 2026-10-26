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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTermsCondition(TransactionCase):
    """Test suite for terms.conditions model (terms_condition.py)."""

    def test_01_single_record_terms_condition(self):
        """Test single record creation and computed terms_id."""
        terms = self.env['terms.conditions'].create({
            'terms_conditions': 'Warranty valid for 10 days upon completion.',
        })
        self.assertEqual(terms.terms_id, str(terms.id))
        self.assertEqual(terms.terms_conditions, 'Warranty valid for 10 days upon completion.')

    def test_02_multi_record_terms_condition_computation(self):
        """Verify terms.conditions computes multi-record without singleton errors."""
        terms_1 = self.env['terms.conditions'].create({
            'terms_conditions': 'Term 1: Payment required on device handover.',
        })
        terms_2 = self.env['terms.conditions'].create({
            'terms_conditions': 'Term 2: Data backup is customer responsibility.',
        })
        terms_3 = self.env['terms.conditions'].create({
            'terms_conditions': 'Term 3: Unclaimed devices after 30 days are subject to disposal.',
        })
        records = terms_1 | terms_2 | terms_3
        # Explicitly trigger compute method across multi-record set
        records._compute_terms_id()

        self.assertEqual(terms_1.terms_id, str(terms_1.id))
        self.assertEqual(terms_2.terms_id, str(terms_2.id))
        self.assertEqual(terms_3.terms_id, str(terms_3.id))
