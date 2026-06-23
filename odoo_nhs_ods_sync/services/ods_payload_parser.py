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
import hashlib
import json
import logging
from datetime import date, datetime

_logger = logging.getLogger(__name__)


def parse_ods_payload(raw: dict) -> dict:
    """
    Input:  raw ODS JSON payload (the value inside the 'Organisation' key).
    Output: dict suitable for ORM write/create on nhs.trust.
    """
    if not raw:
        raise ValueError("Empty ODS payload")

    org_id = raw.get('OrgId', {})
    ods_code = org_id.get('extension', '')
    if not ods_code:
        raise ValueError("ODS payload missing OrgId.extension")

    name = raw.get('Name', '')
    if name.isupper():
        name = name.title()

    raw_status = raw.get('Status', 'Active')
    status = 'active' if raw_status == 'Active' else 'inactive'

    dates = raw.get('Date', [])
    if not isinstance(dates, list):
        dates = [dates]
    operational_start = None
    operational_end = None
    for d in dates:
        if d.get('Type') == 'Operational':
            if d.get('Start'):
                operational_start = _parse_date(d['Start'])
            if d.get('End'):
                operational_end = _parse_date(d['End'])

    geo = raw.get('GeoLoc', {}).get('Location', {})
    addr_parts = [
        geo.get('AddrLn1', ''),
        geo.get('AddrLn2', ''),
        geo.get('AddrLn3', ''),
    ]
    address_line1 = next((a for a in addr_parts if a), '')
    address_line2 = next((a for a in addr_parts[1:] if a), '')
    city = geo.get('Town', '')
    county = geo.get('County', '')
    postcode = geo.get('PostCode', '')
    country = geo.get('Country', '')

    contacts = raw.get('Contacts', {}).get('Contact', [])
    if not isinstance(contacts, list):
        contacts = [contacts]
    phone = next((c.get('value', '') for c in contacts if c.get('type') == 'tel'), '')
    email = next((c.get('value', '') for c in contacts if c.get('type') in ('email', 'mailto')), '')
    if email.lower().startswith('mailto:'):
        email = email[7:]
    website = next((c.get('value', '') for c in contacts if c.get('type') in ('http', 'https')), '')

    roles = raw.get('Roles', {}).get('Role', [])
    if not isinstance(roles, list):
        roles = [roles]

    primary_role_code = None
    all_role_codes = []
    for role in roles:
        code = role.get('id', '')
        if code:
            all_role_codes.append(code)
        if role.get('primaryRole') is True and role.get('Status', 'Active') == 'Active':
            primary_role_code = code

    if not primary_role_code and all_role_codes:
        primary_role_code = all_role_codes[0]

    last_change_raw = raw.get('LastChangeDate', '')
    last_changed_at = _parse_date(last_change_raw) if last_change_raw else None

    active_relations = []
    rels = raw.get('Rels', {}).get('Rel', [])
    if not isinstance(rels, list):
        rels = [rels]
    for rel in rels:
        if isinstance(rel, dict) and rel.get('Status') == 'Active':
            target = rel.get('Target', {})
            if isinstance(target, dict):
                target_org = target.get('OrgId', {})
                if isinstance(target_org, dict):
                    target_code = target_org.get('extension')
                    if target_code:
                        active_relations.append(target_code.upper())

    canonical = json.dumps(raw, sort_keys=True, ensure_ascii=True)
    raw_payload_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    return {
        'name': name,
        'ods_code': ods_code.upper(),
        'status': status,
        'operational_start_date': operational_start,
        'operational_end_date': operational_end,
        'address_line1': address_line1,
        'address_line2': address_line2,
        'city': city,
        'county': county,
        'postcode': postcode,
        'country': country,
        'phone': phone,
        'email': email,
        'website': website,
        'primary_role_code': primary_role_code,
        'all_role_codes': all_role_codes,
        'last_changed_at': last_changed_at,
        'raw_payload_hash': raw_payload_hash,
        'active_relations': active_relations,
    }


def _parse_date(value):
    """Safely parse input value into a date object."""
    if not value:

        return None
    if isinstance(value, (date, datetime)):
        return value if isinstance(value, date) else value.date()
    try:
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None
