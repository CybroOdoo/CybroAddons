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
from datetime import date

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.odoo_nhs_ods_sync.services.ods_payload_parser import parse_ods_payload


def _full_payload():
    """A representative single-organisation ODS payload."""
    return {
        'OrgId': {'extension': 'rw1'},
        'Name': 'BARTS HEALTH NHS TRUST',
        'Status': 'Active',
        'Date': [{'Type': 'Operational', 'Start': '1994-04-01', 'End': '2020-01-01'}],
        'GeoLoc': {'Location': {
            'AddrLn1': 'The Royal London', 'AddrLn2': 'Whitechapel',
            'Town': 'London', 'County': 'Greater London',
            'PostCode': 'E1 1BB', 'Country': 'ENGLAND',
        }},
        'Contacts': {'Contact': [
            {'type': 'tel', 'value': '020 7377 7000'},
            {'type': 'http', 'value': 'https://www.bartshealth.nhs.uk'},
        ]},
        'Roles': {'Role': [
            {'id': 'RO197', 'primaryRole': True, 'Status': 'Active'},
            {'id': 'RO45', 'primaryRole': False},
        ]},
        'Rels': {'Rel': [
            {'Status': 'Active', 'Target': {'OrgId': {'extension': 'qmf'}}},
            {'Status': 'Inactive', 'Target': {'OrgId': {'extension': 'old'}}},
        ]},
        'LastChangeDate': '2026-01-15',
    }


@tagged('post_install', '-at_install')
class TestPayloadParser(TransactionCase):
    """Cover ods_payload_parser.parse_ods_payload — the pure transform from a
    raw ODS JSON payload into an ORM-ready dict."""

    def test_happy_path_full_payload(self):
        """A complete payload maps every field, normalises code/name, and hashes."""
        p = parse_ods_payload(_full_payload())
        self.assertEqual(p['ods_code'], 'RW1')              # uppercased
        self.assertEqual(p['name'], 'Barts Health Nhs Trust')  # title-cased (was ALL CAPS)
        self.assertEqual(p['status'], 'active')
        self.assertEqual(p['operational_start_date'], date(1994, 4, 1))
        self.assertEqual(p['operational_end_date'], date(2020, 1, 1))
        self.assertEqual(p['address_line1'], 'The Royal London')
        self.assertEqual(p['address_line2'], 'Whitechapel')
        self.assertEqual(p['city'], 'London')
        self.assertEqual(p['county'], 'Greater London')
        self.assertEqual(p['postcode'], 'E1 1BB')
        self.assertEqual(p['phone'], '020 7377 7000')
        self.assertEqual(p['website'], 'https://www.bartshealth.nhs.uk')
        self.assertEqual(p['primary_role_code'], 'RO197')
        self.assertEqual(p['all_role_codes'], ['RO197', 'RO45'])
        self.assertEqual(p['active_relations'], ['QMF'])    # only Active rel, uppercased
        self.assertEqual(len(p['raw_payload_hash']), 64)    # sha-256 hex digest

    def test_empty_payload_raises(self):
        """An empty payload is rejected with ValueError."""
        with self.assertRaises(ValueError):
            parse_ods_payload({})

    def test_missing_ods_code_raises(self):
        """A payload without OrgId.extension is rejected with ValueError."""
        with self.assertRaises(ValueError):
            parse_ods_payload({'Name': 'No Code Org'})

    def test_inactive_status_maps_to_inactive(self):
        """A non-'Active' ODS status maps to 'inactive'."""
        raw = _full_payload()
        raw['Status'] = 'Inactive'
        self.assertEqual(parse_ods_payload(raw)['status'], 'inactive')

    def test_primary_role_falls_back_to_first(self):
        """With no flagged primaryRole, the first role code is used."""
        raw = _full_payload()
        raw['Roles'] = {'Role': [
            {'id': 'RO998', 'primaryRole': False},
            {'id': 'RO999', 'primaryRole': False},
        ]}
        self.assertEqual(parse_ods_payload(raw)['primary_role_code'], 'RO998')
