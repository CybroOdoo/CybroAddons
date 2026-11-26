# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
"""Readers for the bank formats CAMT (ISO 20022 XML: camt.052 account
report, camt.053 statement, camt.054 debit/credit notification) and SWIFT
MT940, written from the public format descriptions.

Each reader returns a list of statements::

    {'name': str or None, 'account_number': str or None,
     'currency': ISO code or None,
     'balance_start': float or None, 'balance_end': float or None,
     'transactions': [{'date', 'amount', 'payment_ref', 'partner_name',
                       'account_number', 'ref', 'unique_id',
                       'transaction_details'}]}

and raises ``ValueError`` with a readable message when the file can't be
read. No Odoo dependency, so the readers can be tested on their own.
"""
import re
from datetime import date, datetime

from lxml import etree


def looks_like_camt(data):
    head = data[:2048].lstrip()
    return head.startswith(b'<') and b'camt.05' in data[:4096]


def looks_like_mt940(data):
    return b':20:' in data and b':61:' in data and b':60' in data


# ----------------------------------------------------------------------
# CAMT
# ----------------------------------------------------------------------
def _local(node):
    return etree.QName(node).localname


def _find(node, path):
    """First descendant following ``path`` ('A/B/C', namespace ignored)."""
    for name in path.split('/'):
        if node is None:
            return None
        node = next((child for child in node if isinstance(child.tag, str)
                     and _local(child) == name), None)
    return node


def _find_all(node, path):
    """All nodes following ``path``; the last step may repeat."""
    *parents, last = path.split('/')
    for name in parents:
        node = _find(node, name)
        if node is None:
            return []
    return [child for child in node if isinstance(child.tag, str)
            and _local(child) == last]


def _text(node, *paths):
    """Stripped text of the first path that has one."""
    for path in paths:
        found = _find(node, path) if node is not None else None
        if found is not None and (found.text or '').strip():
            return found.text.strip()
    return None


def _camt_amount(node, sign_node):
    """Signed amount of an Amt node; DBIT is money out."""
    if node is None or not (node.text or '').strip():
        return None, None
    amount = float(node.text.strip())
    if _text(sign_node, 'CdtDbtInd') == 'DBIT':
        amount = -amount
    return amount, node.get('Ccy')


def _camt_date(node, *paths):
    for path in paths:
        value = _text(node, path + '/Dt') or _text(node, path + '/DtTm')
        if value:
            return datetime.strptime(value[:10], '%Y-%m-%d').date()
    return None


def _camt_account(node):
    return _text(node, 'Id/IBAN', 'Id/Othr/Id')


def _camt_party(tx, credit):
    """Name and account of the other party: the debtor of money in, the
    creditor of money out. Name directly under the party (camt.053.001.02)
    or under Pty (later versions)."""
    role = 'Dbtr' if credit else 'Cdtr'
    parties = _find(tx, 'RltdPties')
    if parties is None:
        return None, None
    name = _text(parties, role + '/Nm', role + '/Pty/Nm')
    account = _camt_account(_find(parties, role + 'Acct'))
    return name, account


def _camt_label(tx, entry):
    lines = [(n.text or '').strip() for n in _find_all(tx, 'RmtInf/Ustrd')]
    label = ' '.join(line for line in lines if line)
    reference = _text(tx, 'RmtInf/Strd/CdtrRefInf/Ref')
    return (label or reference or _text(tx, 'AddtlTxInf')
            or _text(entry, 'AddtlNtryInf') or '/'), reference


def _camt_code(node):
    domain = _find(node, 'BkTxCd/Domn')
    if domain is not None:
        return '/'.join(filter(None, [
            _text(domain, 'Cd'), _text(domain, 'Fmly/Cd'),
            _text(domain, 'Fmly/SubFmlyCd')]))
    return _text(node, 'BkTxCd/Prtry/Cd')


def _camt_transaction(entry, tx, amount, entry_date, unique_id):
    credit = amount > 0
    name, account = _camt_party(tx, credit) if tx is not None else (None, None)
    label, reference = _camt_label(tx if tx is not None else entry, entry)
    end_to_end = _text(tx, 'Refs/EndToEndId') if tx is not None else None
    if end_to_end == 'NOTPROVIDED':
        end_to_end = None
    details = {k: v for k, v in {
        'format': 'camt',
        'entry_reference': _text(entry, 'AcctSvcrRef', 'NtryRef'),
        'end_to_end_id': end_to_end,
        'mandate_id': _text(tx, 'Refs/MndtId') if tx is not None else None,
        'bank_code': _camt_code(tx if tx is not None and _find(tx, 'BkTxCd') is not None else entry),
        'value_date': str(_camt_date(entry, 'ValDt') or '') or None,
        'additional_info': _text(entry, 'AddtlNtryInf'),
    }.items() if v}
    return {
        'date': entry_date,
        'amount': amount,
        'payment_ref': label,
        'partner_name': name or False,
        'account_number': account or False,
        'ref': end_to_end or reference or False,
        'unique_id': unique_id or False,
        'transaction_details': details,
    }


def _camt_entries(entry):
    """One transaction per entry, or one per detail when a batch booking
    gives the amount of each."""
    amount, currency = _camt_amount(_find(entry, 'Amt'), entry)
    if amount is None:
        return [], None
    entry_date = _camt_date(entry, 'BookgDt', 'ValDt')
    if not entry_date:
        raise ValueError("An entry has no booking or value date.")
    entry_ref = _text(entry, 'AcctSvcrRef', 'NtryRef')
    details = [tx for block in _find_all(entry, 'NtryDtls')
               for tx in _find_all(block, 'TxDtls')]
    if len(details) > 1:
        rows = []
        for number, tx in enumerate(details, start=1):
            node = _find(tx, 'Amt')
            if node is None:
                node = _find(tx, 'AmtDtls/TxAmt/Amt')
            tx_amount, _currency = _camt_amount(node, tx if _find(tx, 'CdtDbtInd') is not None else entry)
            if tx_amount is None:
                break
            uid = _text(tx, 'Refs/AcctSvcrRef') or (
                entry_ref and '%s-%d' % (entry_ref, number))
            rows.append(_camt_transaction(entry, tx, tx_amount, entry_date, uid))
        else:
            return rows, currency
    tx = details[0] if details else None
    uid = entry_ref or (tx is not None and _text(tx, 'Refs/AcctSvcrRef'))
    return [_camt_transaction(entry, tx, amount, entry_date, uid)], currency


def parse_camt(data):
    try:
        root = etree.fromstring(data, parser=etree.XMLParser(
            resolve_entities=False, no_network=True, huge_tree=False))
    except etree.XMLSyntaxError as error:
        raise ValueError("Cannot read the XML file: %s" % error) from None
    message = next((child for child in root if isinstance(child.tag, str)
                    and _local(child) in ('BkToCstmrStmt', 'BkToCstmrAcctRpt',
                                          'BkToCstmrDbtCdtNtfctn')), None)
    if message is None:
        raise ValueError("This XML file is not a CAMT.052, .053 or .054 "
                         "bank statement.")
    statements = []
    for node in message:
        if not isinstance(node.tag, str) or _local(node) not in ('Stmt', 'Rpt', 'Ntfctn'):
            continue
        account = _find(node, 'Acct')
        currency = _text(account, 'Ccy')
        balances = {}
        for balance in _find_all(node, 'Bal'):
            code = _text(balance, 'Tp/CdOrPrtry/Cd', 'Tp/CdOrPrtry/Prtry')
            amount, ccy = _camt_amount(_find(balance, 'Amt'), balance)
            if code and amount is not None:
                balances.setdefault(code, amount)
                currency = currency or ccy
        transactions = []
        for entry in _find_all(node, 'Ntry'):
            status = _text(entry, 'Sts/Cd', 'Sts')
            if status in ('PDNG', 'INFO'):
                continue
            rows, ccy = _camt_entries(entry)
            transactions += rows
            currency = currency or ccy
        start = balances.get('OPBD', balances.get('PRCD'))
        statements.append({
            'name': _text(node, 'Id'),
            'account_number': _camt_account(account),
            'currency': currency,
            'balance_start': start,
            'balance_end': balances.get('CLBD'),
            'transactions': transactions,
        })
    return statements


# ----------------------------------------------------------------------
# MT940
# ----------------------------------------------------------------------
TAG = re.compile(r'^:(\d{2}[A-Z]?):', re.M)
LINE_61 = re.compile(
    r'^(?P<value>\d{6})(?P<entry>\d{4})?(?P<sign>R?[CD])(?P<fund>[A-Z])?'
    r'(?P<amount>\d+(?:,\d*)?)(?P<type>[NFS][A-Z0-9]{3})'
    r'(?P<customer>[^\n]*?)(?://(?P<bank>[^\n]*))?(?:\n(?P<more>.*))?$', re.S)
BALANCE = re.compile(r'^(?P<sign>[CD])(?P<date>\d{6})(?P<currency>[A-Z]{3})'
                     r'(?P<amount>\d+(?:,\d*)?)')
# Subfield prefixes of the SEPA purpose text (German structured :86:).
SEPA_KEYS = ('EREF', 'KREF', 'MREF', 'CRED', 'DEBT', 'COAM', 'OAMT', 'SVWZ',
             'ABWA', 'ABWE', 'IBAN', 'BIC')
# Tags of the /CODE/value/ form of :86: (Dutch and other SEPA banks).
SLASH_KEYS = ('TRTP', 'IBAN', 'BIC', 'NAME', 'REMI', 'EREF', 'MARF', 'CSID',
              'ADDR', 'ISDT', 'ORDP', 'BENM', 'CNTP', 'PURP', 'ULTC', 'ULTD',
              'SVCL', 'RTRN', 'ID')


def _mt_amount(text):
    return float(text.replace(',', '.') or 0)


def _mt_date(text):
    return date(2000 + int(text[:2]), int(text[2:4]), int(text[4:6]))


def _mt_balance(value):
    match = BALANCE.match(value.strip())
    if not match:
        raise ValueError("Cannot read the balance '%s'." % value.strip())
    amount = _mt_amount(match['amount'])
    return (-amount if match['sign'] == 'D' else amount), match['currency']


def _mt_entry_date(value_date, entry):
    """Booking date MMDD in the year of the value date, across the year
    end when needed."""
    month, day = int(entry[:2]), int(entry[2:])
    year = value_date.year
    if month == 1 and value_date.month == 12:
        year += 1
    elif month == 12 and value_date.month == 1:
        year -= 1
    return date(year, month, day)


def _sepa_purpose(text):
    """Split 'EREF+x SVWZ+y' into {'EREF': 'x', 'SVWZ': 'y'}."""
    parts = re.split(r'(%s)\+' % '|'.join(SEPA_KEYS), text)
    found = {}
    for key, value in zip(parts[1::2], parts[2::2]):
        found[key] = value.strip()
    return found, parts[0].strip()


def _mt_details_german(text):
    fields = {}
    for code, value in re.findall(r'\?(\d{2})([^?]*)', text):
        fields.setdefault(code, []).append(value)
    purpose = ''.join(''.join(fields.get('%02d' % code, []))
                      for code in list(range(20, 30)) + list(range(60, 64)))
    sepa, free = _sepa_purpose(purpose)
    name = ''.join(''.join(fields.get(code, [])) for code in ('32', '33')).strip()
    return {
        'label': sepa.get('SVWZ') or free or purpose.strip()
        or ''.join(fields.get('00', [])).strip(),
        'name': name or None,
        'account': (sepa.get('IBAN') or ''.join(fields.get('31', []))).strip() or None,
        'ref': sepa.get('EREF') if sepa.get('EREF') not in (None, 'NOTPROVIDED') else None,
    }


def _mt_details_slash(text):
    parts = re.split(r'/(%s)/' % '|'.join(SLASH_KEYS), '/' + text.lstrip('/'))
    fields = {}
    for key, value in zip(parts[1::2], parts[2::2]):
        fields.setdefault(key, value.strip().rstrip('/'))
    name, account = fields.get('NAME'), fields.get('IBAN')
    if fields.get('CNTP'):
        # /CNTP/account/BIC/name/city/
        cntp = fields['CNTP'].split('/')
        account = account or (cntp[0] if cntp else None)
        name = name or (cntp[2] if len(cntp) > 2 else None)
    remi = fields.get('REMI') or ''
    for prefix in ('USTD//', 'USTD/', 'STRD/CUR/', 'STRD//', 'STRD/'):
        if remi.startswith(prefix):
            remi = remi[len(prefix):]
            break
    return {
        'label': remi.strip('/ ') or fields.get('TRTP'),
        'name': name or None,
        'account': account or None,
        'ref': fields.get('EREF') if fields.get('EREF') not in (None, 'NOTPROVIDED') else None,
    }


def _mt_details(text):
    """Read the :86: information: German structured (?20..?33), the
    /CODE/value/ form, else free text."""
    lines = [line.strip('\r') for line in text.split('\n')]
    joined = ''.join(lines)
    if re.match(r'^\d{3}\?', joined) or joined.startswith('?'):
        return _mt_details_german(joined)
    if re.match(r'^/?(%s)/' % '|'.join(SLASH_KEYS), joined):
        return _mt_details_slash(joined)
    free = ' '.join(line.strip() for line in lines if line.strip())
    sepa, rest = _sepa_purpose(free)
    if sepa:
        return {'label': sepa.get('SVWZ') or rest or free, 'name': None,
                'account': sepa.get('IBAN'), 'ref': sepa.get('EREF')}
    return {'label': free, 'name': None, 'account': None, 'ref': None}


def _mt_transaction(value):
    match = LINE_61.match(value.strip('\n'))
    if not match:
        raise ValueError("Cannot read the transaction line ':61:%s'." % value.strip())
    value_date = _mt_date(match['value'])
    amount = _mt_amount(match['amount'])
    if match['sign'] in ('D', 'RC'):
        amount = -amount
    customer = (match['customer'] or '').strip()
    bank = (match['bank'] or '').strip()
    more = (match['more'] or '').strip()
    return {
        'date': _mt_entry_date(value_date, match['entry']) if match['entry'] else value_date,
        'amount': amount,
        'payment_ref': more or (customer if customer != 'NONREF' else '') or '/',
        'partner_name': False,
        'account_number': False,
        'ref': customer if customer and customer != 'NONREF' else False,
        'unique_id': bank if bank and bank != 'NONREF' else False,
        'transaction_details': {k: v for k, v in {
            'format': 'mt940', 'type': match['type'], 'customer_reference': customer,
            'bank_reference': bank, 'value_date': str(value_date)}.items() if v},
    }


def parse_mt940(data):
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        text = data.decode('latin-1')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # SWIFT envelope: keep the text block {4: ... -}
    text = re.sub(r'\{[1-3]:[^}]*\}', '', text)
    text = re.sub(r'\{4:\n?', '', text)
    text = re.sub(r'^-\}?\s*$', '', text, flags=re.M)
    text = re.sub(r'\{5:[^}]*\}', '', text)
    pieces = TAG.split(text)
    statements, current, last = [], None, None
    for tag, value in zip(pieces[1::2], pieces[2::2]):
        value = value.rstrip('\n')
        if tag == '20':
            current = {'name': value.strip() or None, 'account_number': None,
                       'currency': None, 'balance_start': None,
                       'balance_end': None, 'transactions': []}
            statements.append(current)
            last = None
            continue
        if current is None:
            raise ValueError("The MT940 file must start each statement with :20:.")
        if tag == '25':
            current['account_number'] = value.strip()
        elif tag == '28C':
            current['name'] = '%s %s' % (current['name'] or '', value.strip()) \
                if current['name'] else value.strip()
        elif tag in ('60F', '60M'):
            current['balance_start'], current['currency'] = _mt_balance(value)
        elif tag in ('62F', '62M'):
            current['balance_end'], currency = _mt_balance(value)
            current['currency'] = current['currency'] or currency
        elif tag == '61':
            last = _mt_transaction(value)
            current['transactions'].append(last)
        elif tag == '86' and last is not None:
            info = _mt_details(value)
            last['transaction_details']['information'] = ' '.join(value.split())
            if info['label']:
                last['payment_ref'] = info['label']
            last['partner_name'] = info['name'] or False
            last['account_number'] = info['account'] or False
            last['ref'] = info['ref'] or last['ref']
            last = None
    if not statements:
        raise ValueError("No statement found in the MT940 file.")
    return statements
