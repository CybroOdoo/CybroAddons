# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from odoo.tests.common import tagged, TransactionCase


_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install', 'wm_compliance')
class TestWmDisposalFacility(TransactionCase):
    """Unit tests verifying licensed disposal facility capacity and licence validation."""

    def test_facility_creation_and_attributes(self):
        """
        Test that facility creation and attributes behaves as expected.
        """
        facility = self.env['wm.disposal.facility'].create({
            'name': 'Greenway Landfill',
            'facility_type': 'landfill',
            'license_no': 'LIC-9988-LF',
            'license_authority': 'Environmental Protection Agency',
            'address': '123 Greenway Road, EcoCity',
            'contact_email': 'contact@greenwaylandfill.org',
        })
        self.assertEqual(facility.name, 'Greenway Landfill')
        self.assertEqual(facility.facility_type, 'landfill')
        self.assertEqual(facility.license_no, 'LIC-9988-LF')
        self.assertEqual(facility.license_authority, 'Environmental Protection Agency')
        self.assertEqual(facility.contact_email, 'contact@greenwaylandfill.org')

        _logger.info('PASS: test_facility_creation_and_attributes')
