""" The sources of the exchange rates. A source fetches the rates of the day against its base currency; the rates are
converted to the currency of each company afterwards, so any base works. Another module adds a source with a class
registered in `PROVIDERS` and in the selection of `res.company.rate_provider`. """
import atexit
import logging
import os
import re
import tempfile
from datetime import UTC, date, datetime, timedelta

import requests
from lxml import etree, html

from odoo.exceptions import UserError
from odoo.tools.misc import file_path

_logger = logging.getLogger(__name__)

TIMEOUT = 20


class RateProvider:
    """ A source of exchange rates. """
    code = None
    name = None
    needs_key = False
    key_field = None  # the field of the company holding the key

    def __init__(self, company):
        self.company = company

    def _get_key(self):
        return self.company.sudo()[self.key_field] if self.key_field else False

    def _hide_key(self, text):
        # the errors of requests show the URL, with the key
        key = self._get_key()
        return text.replace(key, '***') if key else text

    def _get_json(self, url, **params):
        try:
            response = requests.get(url, params=params, timeout=TIMEOUT)
        except requests.RequestException as error:
            raise UserError(self.company.env._('%(provider)s could not be reached: %(error)s',
                              provider=self.name, error=self._hide_key(str(error)))) from error
        try:
            return response.json()
        except ValueError as error:
            raise UserError(self.company.env._('%(provider)s answered with an unexpected response (HTTP %(status)s).',
                              provider=self.name, status=response.status_code)) from error

    def fetch(self):
        """ :return: (date of the rates, base currency code, {currency code: units per 1 base}) """
        raise NotImplementedError()


class EcbProvider(RateProvider):
    code = 'ecb'
    name = 'European Central Bank'
    url = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'

    def fetch(self):
        try:
            response = requests.get(self.url, timeout=TIMEOUT)
            response.raise_for_status()
            root = etree.fromstring(response.content)
        except (requests.RequestException, etree.XMLSyntaxError) as error:
            raise UserError(self.company.env._(
                '%(provider)s could not be reached: %(error)s', provider=self.name, error=error)) from error
        namespace = {'ecb': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
        day = root.find('.//ecb:Cube[@time]', namespace)
        if day is None:
            raise UserError(self.company.env._('%s answered without rates.', self.name))
        rates = {cube.get('currency'): float(cube.get('rate')) for cube in day.findall('ecb:Cube', namespace)}
        return datetime.strptime(day.get('time'), '%Y-%m-%d').date(), 'EUR', rates


class FrankfurterProvider(RateProvider):
    code = 'frankfurter'
    name = 'Frankfurter'
    url = 'https://api.frankfurter.dev/v1/latest'

    def fetch(self):
        data = self._get_json(self.url, base='EUR')
        if not isinstance(data.get('rates'), dict):
            raise UserError(self.company.env._('%(provider)s answered without rates: %(message)s', provider=self.name,
                              message=data.get('message') or data))
        return datetime.strptime(data['date'], '%Y-%m-%d').date(), data['base'], data['rates']


class OpenExchangeRatesProvider(RateProvider):
    code = 'openexchangerates'
    name = 'Open Exchange Rates'
    needs_key = True
    key_field = 'rate_openexchangerates_key'
    url = 'https://openexchangerates.org/api/latest.json'

    def fetch(self):
        key = self._get_key()
        if not key:
            raise UserError(self.company.env._('Enter the App ID of Open Exchange Rates in the settings.'))
        data = self._get_json(self.url, app_id=key)
        if data.get('error') or not isinstance(data.get('rates'), dict):
            raise UserError(self.company.env._('%(provider)s refused the request: %(message)s', provider=self.name,
                              message=data.get('description') or data.get('message') or data))
        day = datetime.fromtimestamp(data['timestamp'], tz=UTC).date()
        return day, data['base'], data['rates']


class ExchangeRateApiProvider(RateProvider):
    code = 'exchangerate_api'
    name = 'ExchangeRate-API'
    key_field = 'rate_exchangerate_api_key'

    def fetch(self):
        key = self._get_key()
        if key:
            data = self._get_json('https://v6.exchangerate-api.com/v6/%s/latest/USD' % key)
        else:
            # the free feed without key, updated once a day
            data = self._get_json('https://open.er-api.com/v6/latest/USD')
        rates = data.get('conversion_rates') or data.get('rates')
        if data.get('result') != 'success' or not isinstance(rates, dict):
            raise UserError(self.company.env._('%(provider)s refused the request: %(message)s', provider=self.name,
                              message=data.get('error-type') or data))
        day = datetime.fromtimestamp(data['time_last_update_unix'], tz=UTC).date()
        return day, data['base_code'], rates


class CentralBankProvider(RateProvider):
    """ The official rates of the central bank chosen on the company, read by one of the `CENTRAL_BANKS`. """
    code = 'central_bank'
    name = 'Central Bank (official rates)'

    def __init__(self, company):
        super().__init__(company)
        self.bank = CENTRAL_BANKS.get(company.rate_central_bank)
        if self.bank:
            # the messages and the source of the rates name the bank
            self.name = self.bank.name

    def fetch(self):
        if not self.bank:
            raise UserError(self.company.env._('Choose the central bank of the Central Bank source in the settings.'))
        return self.bank(self.company).fetch()


# -------------------------------------------------------------------------
# Central banks
# -------------------------------------------------------------------------

_CA_BUNDLES = {}


def _ca_bundle(extra_ca):
    """ The certificates trusted by requests plus `extra_ca`, in a file of this process """
    if extra_ca not in _CA_BUNDLES:
        handle, path = tempfile.mkstemp(prefix='base_accounting_kit_', suffix='.pem')
        with os.fdopen(handle, 'w') as bundle, open(requests.certs.where()) as trusted, \
                open(file_path(extra_ca)) as extra:
            bundle.write(trusted.read() + '\n' + extra.read())
        atexit.register(os.remove, path)
        _CA_BUNDLES[extra_ca] = path
    return _CA_BUNDLES[extra_ca]


MONTHS = {month: number for number, month in enumerate((
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november',
    'december'), start=1)}
# priced by some banks with the currencies, not currencies
METALS = {'XAU', 'XAG', 'XPT', 'XPD'}


def _month(name):
    """ The number of an English month, full or abbreviated ("Oct", "Sept"), else None """
    name = name.lower()
    return next((number for month, number in MONTHS.items() if len(name) >= 3 and month.startswith(name)), None)


def _number(text):
    """ A published figure as a float, None when there is none ("", "N/A", "n/a") """
    try:
        return float(text.replace(',', '').strip())
    except (AttributeError, ValueError):
        return None


class CentralBankReader(RateProvider):
    """ The official rates of a central bank against its currency. A bank is added with a subclass registered in
    `CENTRAL_BANKS`; `fetch` returns the rates in the currency of the bank, see `_from_home_quotes`. """
    country = None  # code of the country whose companies get this bank by default
    country_name = None  # in the list of the banks
    home_currency = None
    decimals = None  # decimals of the published rates, when they are rounded to a fixed number of decimals
    # the firewalls of several banks (SAMA, Bahrain...) refuse the default user agent of requests
    headers = {'User-Agent': 'Odoo'}
    extra_ca = None  # an intermediate certificate the server of the bank does not send

    def _request(self, method, url, **kwargs):
        kwargs.update(timeout=TIMEOUT, headers=self.headers)
        try:
            try:
                response = getattr(requests, method)(url, **kwargs)
            except requests.exceptions.SSLError:
                if not self.extra_ca:
                    raise
                # the chain is completed with the missing intermediate certificate, still fully verified
                response = getattr(requests, method)(url, verify=_ca_bundle(self.extra_ca), **kwargs)
            response.raise_for_status()
        except requests.RequestException as error:
            raise UserError(self.company.env._(
                '%(provider)s could not be reached: %(error)s', provider=self.name, error=error)) from error
        return response

    def _get_page(self, url, **kwargs):
        """ The HTML page of the bank, parsed """
        try:
            return html.fromstring(self._request('get', url, **kwargs).content)
        except etree.ParserError as error:
            raise self._no_rates() from error

    def _get_data(self, method, url, **kwargs):
        """ The JSON answer of the bank """
        try:
            return self._request(method, url, **kwargs).json()
        except ValueError as error:
            raise self._no_rates() from error

    def _no_rates(self):
        return UserError(self.company.env._('%s answered without rates.', self.name))

    def _from_home_quotes(self, quotes, units=None):
        """ {code: units of the home currency per `units[code]` (default 1) code, as published} to
        {code: units of code per 1 home currency} """
        units = units or {}
        rates = {}
        for code, value in quotes.items():
            if code == self.home_currency or code in METALS or not value or value <= 0:
                continue
            if self.decimals and value < 10 ** (2 - self.decimals):
                # fewer than 3 significant digits, e.g. 0.0002 for 1 IDR: too rough, left to the backup source
                continue
            rates[code] = units.get(code, 1) / value
        return rates

    def _from_home_rates(self, rates):
        """ {code: units of code per 1 home currency, as published}, without the home currency, the metals and the
        figures too rough (see `_from_home_quotes`) """
        return {
            code: value for code, value in rates.items()
            if code != self.home_currency and code not in METALS and value and value > 0
            and not (self.decimals and value < 10 ** (2 - self.decimals))
        }


class RbiReader(CentralBankReader):
    """ The reference rates computed by FBIL around 1:30 PM IST each working day, from the archive of the RBI: the
    public pages of FBIL show them a week late. The archive is an ASP.NET form posted with its hidden fields. """
    code = 'rbi'
    name = 'Reserve Bank of India (FBIL reference rates)'
    country = 'IN'
    country_name = 'India'
    home_currency = 'INR'
    url = 'https://www.rbi.org.in/Scripts/ReferenceRateArchive.aspx'
    days = 15  # the period asked, covering the holidays

    def fetch(self):
        form = html.fromstring(self._request('get', self.url).content)
        data = {node.get('name'): node.get('value') or '' for node in form.xpath('//input[@type="hidden"][@name]')}
        today = date.today()
        data.update({
            'chkAll': 'on', 'btnSubmit': ' GO ',
            'txtFromDate': (today - timedelta(days=self.days)).strftime('%d/%m/%Y'),
            'txtToDate': today.strftime('%d/%m/%Y'),
        })
        page = html.fromstring(self._request('post', self.url, data=data).content)
        header = page.xpath('//tr[td[contains(., "INR /")]]')
        if not header:
            raise self._no_rates()
        # e.g. "JPY (INR / 100 JPY)"
        columns = [re.search(r'INR\s*/\s*([\d,]+)\s*([A-Z]{3})', cell.text_content()) for cell in header[0]]
        days = {}
        for row in header[0].itersiblings('tr'):
            cells = [cell.text_content().strip() for cell in row]
            try:
                day = datetime.strptime(cells[0], '%d/%m/%Y').date()
            except (IndexError, ValueError):
                continue
            days[day] = {
                column.group(2): float(value) / float(column.group(1).replace(',', ''))
                for column, value in zip(columns, cells, strict=False) if column and re.fullmatch(r'[\d.]+', value)
            }
        if not days:
            raise self._no_rates()
        day = max(days)
        return day, self.home_currency, self._from_home_quotes(days[day])


class SamaReader(CentralBankReader):
    """ The exchange rates of the Saudi Central Bank (the riyal is pegged at 3.75 per US dollar), in SAR per 1 unit,
    from the JSON its site loads; the newest rates come first. """
    code = 'sama'
    name = 'Saudi Central Bank (SAMA)'
    country = 'SA'
    country_name = 'Saudi Arabia'
    home_currency = 'SAR'
    decimals = 5
    url = 'https://www.sama.gov.sa/en-US/_LAYOUTS/15/SAMA.Portal/PortalHandler.ashx'
    extra_ca = 'base_accounting_kit/data/certs/digicert_global_g2_tls_rsa_sha256_2020_ca1.pem'

    def fetch(self):
        try:
            data = self._request('get', self.url, params={
                'op': 'filterCurrenciesWithCount', 'isArabic': 'false', 'code': '', 'date': '', 'page': 0,
                'limit': 200,
            }).json()
            items = [item for item in data.get('data') or [] if item.get('CurrencyDate') and item.get('CurrencyCode')]
        except (ValueError, AttributeError) as error:
            raise self._no_rates() from error
        if not items:
            raise self._no_rates()
        day = max(item['CurrencyDate'] for item in items)
        quotes = {item['CurrencyCode'].split('=')[0].strip(): item.get('CurrencyRate')
                  for item in items if item['CurrencyDate'] == day}
        return datetime.fromisoformat(day).date(), self.home_currency, self._from_home_quotes(quotes)


class CbuaeReader(CentralBankReader):
    """ The exchange rates of the Central Bank of the UAE, in AED per 1 unit, published each working day around 6 PM
    (UAE) for the VAT: the table its page loads, by currency name. """
    code = 'cbuae'
    name = 'Central Bank of the UAE'
    country = 'AE'
    country_name = 'United Arab Emirates'
    home_currency = 'AED'
    decimals = 6
    url = 'https://centralbank.ae/umbraco/Surface/Exchange/GetExchangeRateAllCurrency'
    # the names of the table, as written by the bank
    currencies = {
        'algerian dinar': 'DZD', 'argentine peso': 'ARS', 'australian dollar': 'AUD', 'azerbaijan manat': 'AZN',
        'bahrani dinar': 'BHD', 'bahraini dinar': 'BHD', 'bangladesh taka': 'BDT', 'belarus rouble': 'BYN',
        'botswana pula': 'BWP', 'brazilian real': 'BRL', 'brunei dollar': 'BND', 'bulgarian lev': 'BGN',
        'canadian dollar': 'CAD', 'chilean peso': 'CLP', 'chinese yuan': 'CNY', 'chinese yuan - offshore': 'CNH',
        'colombian peso': 'COP', 'czech koruna': 'CZK', 'danish krone': 'DKK', 'egypt pound': 'EGP',
        'ethiopian birr': 'ETB', 'euro': 'EUR', 'gb pound': 'GBP', 'hongkong dollar': 'HKD', 'hungarian forint': 'HUF',
        'iceland krona': 'ISK', 'indian rupee': 'INR', 'indonesia rupiah': 'IDR', 'iranian rial': 'IRR',
        'iraqi dinar': 'IQD', 'israeli new shekel': 'ILS', 'japanese yen': 'JPY', 'jordan dinar': 'JOD',
        'kazakhstan tenge': 'KZT', 'kenya shilling': 'KES', 'korean won': 'KRW', 'kuwaiti dinar': 'KWD',
        'lebanon pound': 'LBP', 'libyan dinar': 'LYD', 'macedonia denar': 'MKD', 'malaysia ringgit': 'MYR',
        'mauritian rupee': 'MUR', 'mexican peso': 'MXN', 'moroccan dirham': 'MAD', 'nepalese rupee': 'NPR',
        'newzealand dollar': 'NZD', 'nigerian naira': 'NGN', 'norwegian krone': 'NOK', 'omani rial': 'OMR',
        'pakistan rupee': 'PKR', 'peru sol': 'PEN', 'philippine piso': 'PHP', 'polish zloty': 'PLN',
        'qatari riyal': 'QAR', 'romanian leu': 'RON', 'russia rouble': 'RUB', 'saudi riyal': 'SAR',
        'serbian dinar': 'RSD', 'singapore dollar': 'SGD', 'south africa rand': 'ZAR', 'sri lanka rupee': 'LKR',
        'sudanese pound': 'SDG', 'swedish krona': 'SEK', 'swiss franc': 'CHF', 'syrian pound': 'SYP',
        'taiwan dollar': 'TWD', 'tanzania shilling': 'TZS', 'thai baht': 'THB', 'trin tob dollar': 'TTD',
        'tunisian dinar': 'TND', 'turkish lira': 'TRY', 'turkmen manat': 'TMT', 'uganda shilling': 'UGX',
        'us dollar': 'USD', 'uzbekistani som': 'UZS', 'vietnam dong': 'VND', 'yemen rial': 'YER',
        'zambian kwacha': 'ZMW',
    }
    def fetch(self):
        page = self._get_page(self.url)
        # "Last updated: Friday 30 October 2026 06:05:15 PM"
        updated = re.search(r'Last updated:\s*\w+\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', page.text_content())
        quotes = {}
        for row in page.xpath('//tbody/tr'):
            cells = [cell.text_content().strip() for cell in row]
            if len(cells) < 3:
                continue
            code = self.currencies.get(' '.join(cells[1].lower().split()))
            if not code:
                _logger.info('%s: unknown currency %r', self.name, cells[1])
                continue
            try:
                quotes[code] = float(cells[2])
            except ValueError:
                continue
        if not updated or not _month(updated.group(2)) or not quotes:
            raise self._no_rates()
        day = date(int(updated.group(3)), _month(updated.group(2)), int(updated.group(1)))
        return day, self.home_currency, self._from_home_quotes(quotes)


# Middle East

class CboReader(CentralBankReader):
    """ The exchange rates of the Central Bank of Oman (the rial is pegged at 0.3845 per US dollar), in OMR per 1
    unit, from its exchange rates page. Only buying and selling rates are published: the mid rate is used. """
    code = 'cbo'
    name = 'Central Bank of Oman'
    country = 'OM'
    country_name = 'Oman'
    home_currency = 'OMR'
    decimals = 7
    url = 'https://cbo.gov.om/Pages/DFESearch.aspx'
    extra_ca = 'base_accounting_kit/data/certs/digicert_global_g2_tls_rsa_sha256_2020_ca1.pem'

    def fetch(self):
        page = self._get_page(self.url)
        # "29 / 10 / 2026"
        updated = page.xpath('//span[contains(@class, "lblDate")]')
        match = updated and re.search(r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})', updated[0].text_content())
        quotes = {}
        for row in page.xpath('//table//tr[count(td) >= 5]'):
            # code, name, country, buying, selling, the figures written as "string;#0.384"
            cells = [cell.text_content().strip().replace('string;#', '') for cell in row]
            if len(cells) >= 5 and re.fullmatch(r'[A-Z]{3}', cells[0]):
                buying, selling = _number(cells[3]), _number(cells[4])
                if buying and selling:
                    quotes[cells[0]] = (buying + selling) / 2
        if not match or not quotes:
            raise self._no_rates()
        day = date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
        return day, self.home_currency, self._from_home_quotes(quotes)


class CbkKuwaitReader(CentralBankReader):
    """ The exchange rates of the Central Bank of Kuwait, in fils (1/1000 KWD) per 1 unit, for about 150
    currencies: the full list of its exchange rates page, the code of each currency in its link. """
    code = 'cbk_kuwait'
    name = 'Central Bank of Kuwait'
    country = 'KW'
    country_name = 'Kuwait'
    home_currency = 'KWD'
    decimals = 3  # of the fils
    url = 'https://www.cbk.gov.kw/en/monetary-policy/market-operations/exchange-rates'

    def fetch(self):
        page = self._get_page(self.url, params={'showAll': 'yes'})
        # "Updated | Thu 29.10.2026"
        updated = re.search(r'Updated\s*\|\s*\w*\s*(\d{1,2})\.(\d{1,2})\.(\d{4})', page.text_content())
        quotes = {}
        for block in page.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " list-rate ")]'):
            link = block.xpath('.//a[contains(@class, "link-rate")]/@href')
            value = block.xpath('.//li[contains(@class, "col-val")][1]/span[contains(@class, "val")]')
            code = link and link[0].rstrip('/').rsplit('/', 1)[-1].upper()
            if code and re.fullmatch(r'[A-Z]{3}', code) and value:
                quotes[code] = _number(value[0].text_content())
        if not updated or not quotes:
            raise self._no_rates()
        day = date(int(updated.group(3)), int(updated.group(2)), int(updated.group(1)))
        return day, self.home_currency, self._from_home_quotes(quotes, dict.fromkeys(quotes, 1000))


class CbbReader(CentralBankReader):
    """ The exchange rates of the Central Bank of Bahrain (the dinar is pegged to the US dollar), in BHD per 1 unit,
    from the table of its rates page. """
    code = 'cbb'
    name = 'Central Bank of Bahrain'
    country = 'BH'
    country_name = 'Bahrain'
    home_currency = 'BHD'
    decimals = 6
    url = 'https://www.cbb.gov.bh/facilities-interest-rates/'

    def fetch(self):
        page = self._get_page(self.url)
        table = page.xpath('//table[.//td[contains(., "EXCHANGE RATES")]]')
        if not table:
            raise self._no_rates()
        # "29 Oct 2026 - EXCHANGE RATES"
        updated = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s*-\s*EXCHANGE RATES', table[0].text_content())
        quotes = {}
        for row in table[0].xpath('.//tr'):
            cells = [cell.text_content().strip() for cell in row]
            # "USD✱": the peg
            code = len(cells) == 2 and re.sub(r'[^A-Z]', '', cells[0])
            if code and len(code) == 3 and _number(cells[1]):
                quotes[code] = _number(cells[1])
        if not updated or not _month(updated.group(2)) or not quotes:
            raise self._no_rates()
        day = date(int(updated.group(3)), _month(updated.group(2)), int(updated.group(1)))
        return day, self.home_currency, self._from_home_quotes(quotes)


class CbjReader(CentralBankReader):
    """ The exchange rates of the Central Bank of Jordan (the dinar is pegged to the US dollar), in fils (1/1000
    JOD) per 1 unit (per 100 yen), for 5 currencies; the newest day comes first. Only the lowest and highest rates
    are published: the mid rate is used. """
    code = 'cbj'
    name = 'Central Bank of Jordan'
    country = 'JO'
    country_name = 'Jordan'
    home_currency = 'JOD'
    decimals = 2  # of the fils
    url = 'https://www.cbj.gov.jo/En/Pages/foreignexchangerates'
    aliases = {'YEN': 'JPY'}

    def fetch(self):
        page = self._get_page(self.url)
        table = page.xpath('//table[.//span[contains(., "Foreign Exchange Rates")]]')
        if not table:
            raise self._no_rates()
        # "2026/10/29"
        updated = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', table[0].text_content())
        quotes, units = {}, {}
        for row in table[0].xpath('.//tbody/tr'):
            cells = [cell.text_content().strip() for cell in row]
            # logo, currency ("USD", "YEN 100"), lowest, highest
            match = len(cells) == 4 and re.fullmatch(r'([A-Z]{3})\s*(\d*)', cells[1])
            if match and _number(cells[2]) and _number(cells[3]):
                code = self.aliases.get(match.group(1), match.group(1))
                quotes[code] = (_number(cells[2]) + _number(cells[3])) / 2
                units[code] = int(match.group(2) or 1) * 1000
        if not updated or not quotes:
            raise self._no_rates()
        day = date(int(updated.group(1)), int(updated.group(2)), int(updated.group(3)))
        return day, self.home_currency, self._from_home_quotes(quotes, units)


class BoiReader(CentralBankReader):
    """ The representative rates of the Bank of Israel, in ILS per 1 unit (or per 10, 100), set each business day
    around 3:30 PM (Israel), from its public API. """
    code = 'boi'
    name = 'Bank of Israel'
    country = 'IL'
    country_name = 'Israel'
    home_currency = 'ILS'
    decimals = 4
    url = 'https://boi.org.il/PublicApi/GetExchangeRates'

    def fetch(self):
        data = self._get_data('get', self.url)
        items = [item for item in (data.get('exchangeRates') if isinstance(data, dict) else None) or []
                 if isinstance(item, dict) and item.get('key') and item.get('lastUpdate')]
        if not items:
            raise self._no_rates()
        # "2026-10-30T10:21:03.7731459Z": the time of the rates, about noon in UTC
        day = max(item['lastUpdate'][:10] for item in items)
        quotes = {item['key']: item.get('currentExchangeRate') for item in items}
        units = {item['key']: item.get('unit') or 1 for item in items}
        return date.fromisoformat(day), self.home_currency, self._from_home_quotes(quotes, units)


# Africa and South Asia

class BangladeshBankReader(CentralBankReader):
    """ The exchange rates of Bangladesh Bank, in BDT per 1 unit: the weighted average interbank rate of the US
    dollar and the cross rates of 10 currencies, for which only bid and ask rates are published (the mid rate is
    used). """
    code = 'bangladesh_bank'
    name = 'Bangladesh Bank'
    country = 'BD'
    country_name = 'Bangladesh'
    home_currency = 'BDT'
    decimals = 4
    url = 'https://www.bb.org.bd/en/index.php/econdata/exchangerate'
    # quoted the other way among the cross rates: units of the currency per 1 BDT (2.68 LKR for 1 BDT)
    per_taka = {'LKR'}

    def fetch(self):
        page = self._get_page(self.url)
        # "Exchange Rate of Taka  (Oct 29, 2026)"
        updated = re.search(r'Exchange Rate of Taka\s*\(\s*([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})\s*\)',
                            ' '.join(page.text_content().split()))
        quotes = {}
        for row in page.xpath('//table//tbody/tr'):
            cells = [cell.text_content().strip() for cell in row]
            if not cells or not re.fullmatch(r'[A-Z]{3}', cells[0]):
                continue
            if len(cells) >= 4 and _number(cells[3]):
                # the weighted average rate of the US dollar
                quotes[cells[0]] = _number(cells[3])
            elif len(cells) >= 3 and _number(cells[1]) and _number(cells[2]):
                quotes[cells[0]] = (_number(cells[1]) + _number(cells[2])) / 2
        if not updated or not _month(updated.group(1)) or not quotes:
            raise self._no_rates()
        day = date(int(updated.group(3)), _month(updated.group(1)), int(updated.group(2)))
        rates = self._from_home_quotes({code: value for code, value in quotes.items() if code not in self.per_taka})
        rates.update(self._from_home_rates({code: value for code, value in quotes.items() if code in self.per_taka}))
        return day, self.home_currency, rates


class CbnReader(CentralBankReader):
    """ The official central rates of the Central Bank of Nigeria, in NGN per 1 unit, for 10 currencies, from the
    JSON of the recent days its rates page loads. """
    code = 'cbn'
    name = 'Central Bank of Nigeria'
    country = 'NG'
    country_name = 'Nigeria'
    home_currency = 'NGN'
    decimals = 4
    # the full history is GetAllExchangeRates, 8 MB: this one holds the last weeks
    url = 'https://www.cbn.gov.ng/api/GetAllExchangeRatesGRAPH'
    # the names of the bank; the CFA franc (XOF or XAF?) and the WAUA are left out
    currencies = {
        'us dollar': 'USD', 'pounds sterling': 'GBP', 'euro': 'EUR', 'swiss franc': 'CHF', 'yen': 'JPY',
        'yuan/renminbi': 'CNY', 'danish krona': 'DKK', 'riyal': 'SAR', 'uae dirham': 'AED',
        'south african rand': 'ZAR', 'sdr': 'XDR',
    }

    def fetch(self):
        data = self._get_data('get', self.url)
        items = [item for item in (data if isinstance(data, list) else [])
                 if isinstance(item, dict) and item.get('ratedate') and item.get('currency')]
        if not items:
            raise self._no_rates()
        day = max(item['ratedate'] for item in items)
        quotes = {}
        for item in items:
            code = self.currencies.get(' '.join(item['currency'].lower().split()))
            if item['ratedate'] == day and code:
                quotes[code] = _number(item.get('centralrate'))
        return date.fromisoformat(day[:10]), self.home_currency, self._from_home_quotes(quotes)


class CbkKenyaReader(CentralBankReader):
    """ The indicative rates of the Central Bank of Kenya (trade weighted averages), in KES per 1 unit, for about 20
    currencies, from the table its forex page loads; the East African currencies are quoted per 1 KES. """
    code = 'cbk_kenya'
    name = 'Central Bank of Kenya'
    country = 'KE'
    country_name = 'Kenya'
    home_currency = 'KES'
    decimals = 4
    url = 'https://www.centralbank.go.ke/wp-admin/admin-ajax.php'
    # the table of the indicative rates; the one shown first on the page stopped in 2024
    table = 193
    currencies = {
        'us dollar': 'USD', 'stg pound': 'GBP', 'euro': 'EUR', 'sa rand': 'ZAR', 'ae dirham': 'AED',
        'can $': 'CAD', 's franc': 'CHF', 'jpy (100)': 'JPY', 'sw kroner': 'SEK', 'nor kroner': 'NOK',
        'dan kroner': 'DKK', 'ind rupee': 'INR', 'hongkong dollar': 'HKD', 'singapore dollar': 'SGD',
        'saudi riyal': 'SAR', 'chinese yuan': 'CNY', 'australian $': 'AUD',
    }
    # quoted the other way: units of the currency per 1 KES
    per_shilling = {'kes / ushs': 'UGX', 'kes / tshs': 'TZS', 'kes / rwf': 'RWF', 'kes / bif': 'BIF'}

    def fetch(self):
        # the request of the table, newest first: a page holds the 21 currencies of a day twice over
        data = {'draw': 1, 'start': 0, 'length': 50, 'order[0][column]': 0, 'order[0][dir]': 'desc'}
        for column in range(3):
            data.update({'columns[%s][data]' % column: column, 'columns[%s][orderable]' % column: 'true'})
        answer = self._get_data('post', self.url, params={'action': 'get_wdtable', 'table_id': self.table},
                                data=data)
        days = {}
        for row in (answer.get('data') if isinstance(answer, dict) else None) or []:
            # "30/10/2026", "US DOLLAR", "129.9500"
            try:
                day = datetime.strptime(row[0], '%d/%m/%Y').date()
            except (IndexError, TypeError, ValueError):
                continue
            days.setdefault(day, {})[' '.join(str(row[1]).lower().split())] = _number(row[2])
        if not days:
            raise self._no_rates()
        day = max(days)
        quotes, units = {}, {}
        for name, value in days[day].items():
            if name in self.currencies:
                code = self.currencies[name]
                quotes[code], units[code] = value, 100 if code == 'JPY' else 1
        rates = self._from_home_quotes(quotes, units)
        rates.update({code: days[day][name] for name, code in self.per_shilling.items() if days[day].get(name)})
        return day, self.home_currency, rates


class CbslReader(CentralBankReader):
    """ The indicative exchange rates of the Central Bank of Sri Lanka, in LKR per 1 unit, for about 60
    currencies, from its exchange rates form posted for the last days with every currency. """
    code = 'cbsl'
    name = 'Central Bank of Sri Lanka'
    country = 'LK'
    country_name = 'Sri Lanka'
    home_currency = 'LKR'
    decimals = 4
    form_url = 'https://www.cbsl.gov.lk/cbsl_custom/exrates/exrates.php'
    url = 'https://www.cbsl.gov.lk/cbsl_custom/exrates/exrates_results.php'
    days = 10  # the period asked, covering the holidays

    def fetch(self):
        form = self._get_page(self.form_url)
        currencies = form.xpath('//input[@name="chk_cur[]"]/@value')
        if not currencies:
            raise self._no_rates()
        today = date.today()
        data = [
            ('lookupPage', 'lookup_daily_exchange_rates.php'), ('startRange', '2006-11-11'), ('rangeType', 'dates'),
            ('txtStart', (today - timedelta(days=self.days)).isoformat()), ('txtEnd', today.isoformat()),
        ] + [('chk_cur[]', currency) for currency in currencies] + [('submit_button', 'Submit')]
        page = html.fromstring(self._request('post', self.url, data=data).content)
        days = {}
        # a table by currency, "Date | 1 USD -> LKR | 1 LKR -> USD", newest day first
        for table in page.xpath('//table'):
            header = re.search(r'1\s+([A-Z]{3})\s*->\s*LKR', table.text_content())
            if not header:
                continue
            for row in table.xpath('.//tr'):
                cells = [cell.text_content().strip() for cell in row]
                if len(cells) >= 2 and re.fullmatch(r'\d{4}-\d{2}-\d{2}', cells[0]):
                    days.setdefault(cells[0], {})[header.group(1)] = _number(cells[1])
        if not days:
            raise self._no_rates()
        day = max(days)
        return date.fromisoformat(day), self.home_currency, self._from_home_quotes(days[day])


# Europe and Central Asia

class TcmbReader(CentralBankReader):
    """ The indicative exchange rates of the Central Bank of the Republic of Türkiye, in TRY per 1 unit (per 100
    yen), set each working day at 3:30 PM (Türkiye), from its daily XML. Only buying and selling rates are
    published: the mid of the forex rates is used. """
    code = 'tcmb'
    name = 'Central Bank of the Republic of Türkiye'
    country = 'TR'
    country_name = 'Türkiye'
    home_currency = 'TRY'
    decimals = 4
    url = 'https://www.tcmb.gov.tr/kurlar/today.xml'

    def fetch(self):
        try:
            root = etree.fromstring(self._request('get', self.url).content)
            day = datetime.strptime(root.get('Tarih') or '', '%d.%m.%Y').date()
        except (etree.XMLSyntaxError, ValueError) as error:
            raise self._no_rates() from error
        quotes, units = {}, {}
        for currency in root.iter('Currency'):
            code = currency.get('CurrencyCode')
            buying, selling = _number(currency.findtext('ForexBuying')), _number(currency.findtext('ForexSelling'))
            if code and buying and selling:
                quotes[code] = (buying + selling) / 2
                units[code] = int(_number(currency.findtext('Unit')) or 1)
        if not quotes:
            raise self._no_rates()
        return day, self.home_currency, self._from_home_quotes(quotes, units)


class NbpReader(CentralBankReader):
    """ The average exchange rates of Narodowy Bank Polski (table A), in PLN per 1 unit, for about 30 currencies,
    published each working day around noon (Poland), from its API. """
    code = 'nbp'
    name = 'Narodowy Bank Polski (NBP)'
    country = 'PL'
    country_name = 'Poland'
    home_currency = 'PLN'
    url = 'https://api.nbp.pl/api/exchangerates/tables/A'

    def fetch(self):
        data = self._get_data('get', self.url, params={'format': 'json'})
        table = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else {}
        if not table.get('effectiveDate') or not table.get('rates'):
            raise self._no_rates()
        quotes = {rate.get('code'): rate.get('mid') for rate in table['rates']}
        return date.fromisoformat(table['effectiveDate']), self.home_currency, self._from_home_quotes(quotes)


class CnbReader(CentralBankReader):
    """ The exchange rate fixing of the Czech National Bank, in CZK per amount (1, 100 or 1000 units), for about
    30 currencies, set each working day at 2:30 PM (Prague), from its daily text file. """
    code = 'cnb'
    name = 'Czech National Bank'
    country = 'CZ'
    country_name = 'Czech Republic'
    home_currency = 'CZK'
    decimals = 3
    url = ('https://www.cnb.cz/en/financial-markets/foreign-exchange-market/central-bank-exchange-rate-fixing/'
           'central-bank-exchange-rate-fixing/daily.txt')

    def fetch(self):
        lines = self._request('get', self.url).content.decode('utf-8', 'replace').splitlines()
        # "30 Oct 2026 #209", then "Country|Currency|Amount|Code|Rate"
        updated = lines and re.match(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', lines[0])
        quotes, units = {}, {}
        for line in lines[2:]:
            cells = line.split('|')
            if len(cells) == 5 and re.fullmatch(r'[A-Z]{3}', cells[3]) and _number(cells[2]):
                quotes[cells[3]], units[cells[3]] = _number(cells[4]), _number(cells[2])
        if not updated or not _month(updated.group(2)) or not quotes:
            raise self._no_rates()
        day = date(int(updated.group(3)), _month(updated.group(2)), int(updated.group(1)))
        return day, self.home_currency, self._from_home_quotes(quotes, units)


class BnrReader(CentralBankReader):
    """ The reference rates of the National Bank of Romania, in RON per 1 unit (or per multiplier), for about 35
    currencies, set each working day around 1 PM (Romania), from its daily XML. """
    code = 'bnr'
    name = 'National Bank of Romania'
    country = 'RO'
    country_name = 'Romania'
    home_currency = 'RON'
    decimals = 4
    url = 'https://curs.bnr.ro/nbrfxrates.xml'

    def fetch(self):
        try:
            root = etree.fromstring(self._request('get', self.url).content)
        except etree.XMLSyntaxError as error:
            raise self._no_rates() from error
        cube = next(root.iter('{*}Cube'), None)
        if cube is None or not cube.get('date'):
            raise self._no_rates()
        quotes, units = {}, {}
        for rate in cube.iter('{*}Rate'):
            code = rate.get('currency')
            quotes[code], units[code] = _number(rate.text), int(rate.get('multiplier') or 1)
        return date.fromisoformat(cube.get('date')), self.home_currency, self._from_home_quotes(quotes, units)


class MnbReader(CentralBankReader):
    """ The official exchange rates of the Magyar Nemzeti Bank, in HUF per 1 unit (or per 100), for about 30
    currencies, set each working day around noon (Budapest), from its daily rates page: its web service is
    served without TLS. """
    code = 'mnb'
    name = 'Magyar Nemzeti Bank'
    country = 'HU'
    country_name = 'Hungary'
    home_currency = 'HUF'
    decimals = 2
    url = 'https://www.mnb.hu/en/arfolyamok'

    def fetch(self):
        page = self._get_page(self.url)
        tables = page.xpath('//table[.//th[contains(., "Currency")] or .//td[contains(., "Currency")]]')
        quotes, units = {}, {}
        for row in (row for table in tables for row in table.xpath('.//tr')):
            # code, name, unit, value
            cells = [cell.text_content().strip() for cell in row]
            if len(cells) == 4 and re.fullmatch(r'[A-Z]{3}', cells[0]) and _number(cells[2]):
                quotes[cells[0]], units[cells[0]] = _number(cells[3]), _number(cells[2])
        # "Napi árfolyamok: 30 October 2026", the caption of the tables
        updated = tables and re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', tables[0].text_content())
        if not updated or not _month(updated.group(2)) or not quotes:
            raise self._no_rates()
        day = date(int(updated.group(3)), _month(updated.group(2)), int(updated.group(1)))
        return day, self.home_currency, self._from_home_quotes(quotes, units)


class NbuReader(CentralBankReader):
    """ The official exchange rates of the National Bank of Ukraine, in UAH per 1 unit, for about 40 currencies,
    set in the afternoon for the next working day, from its JSON. """
    code = 'nbu'
    name = 'National Bank of Ukraine'
    country = 'UA'
    country_name = 'Ukraine'
    home_currency = 'UAH'
    url = 'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange'

    def fetch(self):
        data = self._get_data('get', self.url, params={'json': ''})
        items = [item for item in (data if isinstance(data, list) else [])
                 if isinstance(item, dict) and item.get('cc') and item.get('exchangedate')]
        if not items:
            raise self._no_rates()
        # "02.11.2026": the day the rates apply from
        days = {datetime.strptime(item['exchangedate'], '%d.%m.%Y').date() for item in items}
        day = max(days)
        quotes = {item['cc']: item.get('rate') for item in items
                  if datetime.strptime(item['exchangedate'], '%d.%m.%Y').date() == day}
        return day, self.home_currency, self._from_home_quotes(quotes)


class NbgReader(CentralBankReader):
    """ The official exchange rates of the National Bank of Georgia, in GEL per quantity (1, 10, 100... units), for
    about 40 currencies, set each working day around 5 PM (Tbilisi) for the next day, from its JSON. """
    code = 'nbg'
    name = 'National Bank of Georgia'
    country = 'GE'
    country_name = 'Georgia'
    home_currency = 'GEL'
    decimals = 4
    url = 'https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/en/json'

    def fetch(self):
        data = self._get_data('get', self.url)
        day = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else {}
        if not day.get('date') or not day.get('currencies'):
            raise self._no_rates()
        quotes = {currency.get('code'): currency.get('rate') for currency in day['currencies']}
        units = {currency.get('code'): currency.get('quantity') or 1 for currency in day['currencies']}
        # "2026-10-31T00:00:00.000Z": the day the rates apply from
        return date.fromisoformat(day['date'][:10]), self.home_currency, self._from_home_quotes(quotes, units)


class NbkReader(CentralBankReader):
    """ The official exchange rates of the National Bank of Kazakhstan, in KZT per quantity (1, 10, 100... units),
    for about 50 currencies, from its RSS feed. """
    code = 'nbk'
    name = 'National Bank of Kazakhstan'
    country = 'KZ'
    country_name = 'Kazakhstan'
    home_currency = 'KZT'
    decimals = 2
    url = 'https://nationalbank.kz/rss/rates_all.xml'

    def fetch(self):
        try:
            root = etree.fromstring(self._request('get', self.url).content)
        except etree.XMLSyntaxError as error:
            raise self._no_rates() from error
        days = {}
        for item in root.iter('item'):
            # AUD, 31.10.2026, 319.34, 1
            try:
                day = datetime.strptime(item.findtext('pubDate') or '', '%d.%m.%Y').date()
            except ValueError:
                continue
            days.setdefault(day, {})[item.findtext('title')] = (
                _number(item.findtext('description')), _number(item.findtext('quant')) or 1)
        if not days:
            raise self._no_rates()
        day = max(days)
        quotes = {code: value for code, (value, quantity) in days[day].items()}
        units = {code: quantity for code, (value, quantity) in days[day].items()}
        return day, self.home_currency, self._from_home_quotes(quotes, units)


class BoeReader(CentralBankReader):
    """ The daily spot exchange rates of the Bank of England, in units of 25 currencies per 1 GBP, observed around
    4 PM (London) and added to its database the next working day, from the CSV export of the database. """
    code = 'boe'
    name = 'Bank of England'
    country = 'GB'
    country_name = 'United Kingdom'
    home_currency = 'GBP'
    decimals = 4
    url = 'https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp'
    days = 10  # the period asked, covering the holidays
    # the codes of the series of the spot rates in the database
    series = {
        'XUDLADS': 'AUD', 'XUDLCDS': 'CAD', 'XUDLBK89': 'CNY', 'XUDLBK25': 'CZK', 'XUDLDKS': 'DKK',
        'XUDLERS': 'EUR', 'XUDLHDS': 'HKD', 'XUDLBK33': 'HUF', 'XUDLBK97': 'INR', 'XUDLBK78': 'ILS',
        'XUDLJYS': 'JPY', 'XUDLBK83': 'MYR', 'XUDLNDS': 'NZD', 'XUDLNKS': 'NOK', 'XUDLBK47': 'PLN',
        'XUDLSRS': 'SAR', 'XUDLSGS': 'SGD', 'XUDLZRS': 'ZAR', 'XUDLBK93': 'KRW', 'XUDLSKS': 'SEK',
        'XUDLSFS': 'CHF', 'XUDLTWS': 'TWD', 'XUDLBK87': 'THB', 'XUDLBK95': 'TRY', 'XUDLUSS': 'USD',
    }

    def fetch(self):
        start = date.today() - timedelta(days=self.days)
        response = self._request('get', self.url, params={
            'csv.x': 'yes', 'SeriesCodes': ','.join(self.series), 'UsingCodes': 'Y', 'CSVF': 'TN', 'VPD': 'Y',
            'VFD': 'N', 'Dateto': 'now',
            # "21/Oct/2026", in English whatever the locale
            'Datefrom': '%02d/%s/%d' % (start.day, list(MONTHS)[start.month - 1][:3].title(), start.year),
        })
        # "DATE,XUDLADS,...", then "30 Oct 2026,1.8925,..." by day
        lines = response.content.decode('utf-8', 'replace').splitlines()
        header = lines[0].split(',') if lines else []
        days = {}
        for line in lines[1:]:
            cells = line.split(',')
            match = re.fullmatch(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', cells[0].strip())
            if match and _month(match.group(2)):
                day = date(int(match.group(3)), _month(match.group(2)), int(match.group(1)))
                days[day] = {self.series[code]: _number(value)
                             for code, value in zip(header[1:], cells[1:], strict=False) if code in self.series}
        if header[:1] != ['DATE'] or not days:
            raise self._no_rates()
        day = max(days)
        return day, self.home_currency, self._from_home_rates(days[day])


class SnbReader(CentralBankReader):
    """ The exchange rates of the Swiss National Bank at 11 AM (Zurich), in CHF per 1 unit (per 100 yen), for the
    euro, the US dollar, the pound sterling and the yen, from its RSS feed of the last days. """
    code = 'snb'
    name = 'Swiss National Bank'
    country = 'CH'
    country_name = 'Switzerland'
    home_currency = 'CHF'
    decimals = 4
    url = 'https://www.snb.ch/public/en/rss/exchangeRates'

    def fetch(self):
        try:
            root = etree.fromstring(self._request('get', self.url).content)
        except etree.XMLSyntaxError as error:
            raise self._no_rates() from error
        days = {}
        for title in root.iterfind('.//item/title'):
            # "CH: 0.5222 CHF = 100 JPY 2026-10-30 Daily rates (11:00)"
            match = re.match(r'CH:\s*([\d.]+)\s*CHF\s*=\s*(\d+)\s*([A-Z]{3})\s+(\d{4}-\d{2}-\d{2})', title.text or '')
            if match:
                days.setdefault(match.group(4), {})[match.group(3)] = (float(match.group(1)), int(match.group(2)))
        if not days:
            raise self._no_rates()
        day = max(days)
        quotes = {code: value for code, (value, unit) in days[day].items()}
        units = {code: unit for code, (value, unit) in days[day].items()}
        return date.fromisoformat(day), self.home_currency, self._from_home_quotes(quotes, units)


class NorgesBankReader(CentralBankReader):
    """ The exchange rates of Norges Bank, in NOK per 1 unit (or per 100), for about 40 currencies, set each
    business day around 4 PM (Oslo), from the SDMX-JSON of its open data API. """
    code = 'norges_bank'
    name = 'Norges Bank'
    country = 'NO'
    country_name = 'Norway'
    home_currency = 'NOK'
    url = 'https://data.norges-bank.no/api/data/EXR/B..NOK.SP'
    indices = {'TWI', 'I44'}  # the trade-weighted indices, not currencies

    def fetch(self):
        data = self._get_data('get', self.url, params={'lastNObservations': 1, 'format': 'sdmx-json'})
        # the last observation of each series, the currencies and the multipliers indexed in the structure
        observations = {}
        try:
            structure = data['data']['structure']
            dimensions = structure['dimensions']['series']
            position = next(index for index, dimension in enumerate(dimensions) if dimension['id'] == 'BASE_CUR')
            currencies = [value['id'] for value in dimensions[position]['values']]
            periods = [value['id'] for value in structure['dimensions']['observation'][0]['values']]
            attributes = structure['attributes']['series']
            multiplier = next(index for index, attribute in enumerate(attributes) if attribute['id'] == 'UNIT_MULT')
            multipliers = [int(value['id']) for value in attributes[multiplier]['values']]
            for key, series in data['data']['dataSets'][0]['series'].items():
                code = currencies[int(key.split(':')[position])]
                if code in self.indices:
                    continue
                unit = 10 ** multipliers[series['attributes'][multiplier]]
                for period, values in series['observations'].items():
                    observations.setdefault(periods[int(period)], {})[code] = (_number(values[0]), unit)
        except (KeyError, IndexError, TypeError, ValueError, StopIteration) as error:
            raise self._no_rates() from error
        if not observations:
            raise self._no_rates()
        # the series no longer published stop at an older day
        day = max(observations)
        quotes = {code: value for code, (value, unit) in observations[day].items()}
        units = {code: unit for code, (value, unit) in observations[day].items()}
        return date.fromisoformat(day), self.home_currency, self._from_home_quotes(quotes, units)


class RiksbankReader(CentralBankReader):
    """ The mid-market exchange rates of Sveriges Riksbank, in SEK per 1 unit, for about 30 currencies, from the
    latest observations of its open API (without key, within its limit of calls). """
    code = 'riksbank'
    name = 'Sveriges Riksbank'
    country = 'SE'
    country_name = 'Sweden'
    home_currency = 'SEK'
    decimals = 5
    url = 'https://api.riksbank.se/swea/v1/Observations/Latest/ByGroup/130'

    def fetch(self):
        data = self._get_data('get', self.url)
        # {"seriesId": "SEKUSDPMI", "date": "2026-10-30", "value": 9.82635}
        items = [item for item in (data if isinstance(data, list) else [])
                 if isinstance(item, dict) and item.get('date')
                 and re.fullmatch(r'SEK[A-Z]{3}PMI', str(item.get('seriesId')))]
        if not items:
            raise self._no_rates()
        # the series no longer published (the currencies replaced by the euro...) stop at an older day
        day = max(item['date'] for item in items)
        quotes = {item['seriesId'][3:6]: item.get('value') for item in items if item['date'] == day}
        return date.fromisoformat(day), self.home_currency, self._from_home_quotes(quotes)


class DanmarksNationalbankReader(CentralBankReader):
    """ The exchange rates of Danmarks Nationalbank, in DKK per 100 units, for about 30 currencies, published each
    banking day in the afternoon, from its daily XML. """
    code = 'danmarks_nationalbank'
    name = 'Danmarks Nationalbank'
    country = 'DK'
    country_name = 'Denmark'
    home_currency = 'DKK'
    url = 'https://www.nationalbanken.dk/api/currencyratesxml'

    def fetch(self):
        try:
            root = etree.fromstring(self._request('get', self.url, params={'lang': 'en'}).content)
        except etree.XMLSyntaxError as error:
            raise self._no_rates() from error
        # <dailyrates id="2026-10-30"><currency code="USD" desc="US dollars" rate="668.95"/>
        rates = root.find('dailyrates')
        if rates is None or not rates.get('id'):
            raise self._no_rates()
        quotes = {currency.get('code'): _number(currency.get('rate')) for currency in rates.iter('currency')}
        if not quotes:
            raise self._no_rates()
        return (date.fromisoformat(rates.get('id')), self.home_currency,
                self._from_home_quotes(quotes, dict.fromkeys(quotes, 100)))


class SedlabankiReader(CentralBankReader):
    """ The official reference rates (mid rates) of the Central Bank of Iceland, in ISK per 1 unit, for 9
    currencies and the SDR, from the XML of its time series. """
    code = 'sedlabanki'
    name = 'Central Bank of Iceland'
    country = 'IS'
    country_name = 'Iceland'
    home_currency = 'ISK'
    url = 'https://www.sedlabanki.is/xmltimeseries/Default.aspx'
    group = 9  # the official reference rates
    days = 10  # the period asked, covering the holidays
    # the series of the mid rates ("miðgengi") in the group
    series = {
        '4055': 'USD', '4061': 'DKK', '4064': 'EUR', '4085': 'JPY', '4088': 'CAD', '4091': 'NOK', '4097': 'XDR',
        '4103': 'GBP', '4106': 'CHF', '4109': 'SEK',
    }

    def fetch(self):
        today = date.today()
        try:
            root = etree.fromstring(self._request('get', self.url, params={
                'DagsFra': (today - timedelta(days=self.days)).isoformat(), 'DagsTil': today.isoformat(),
                'GroupID': self.group, 'Type': 'xml'}).content)
        except etree.XMLSyntaxError as error:
            raise self._no_rates() from error
        days = {}
        for series in root.iter('TimeSeries'):
            code = self.series.get(series.get('ID'))
            for entry in series.iter('Entry') if code else ():
                # "10/30/2026 12:00:00 AM"
                try:
                    day = datetime.strptime((entry.findtext('Date') or '').split()[0], '%m/%d/%Y').date()
                except (IndexError, ValueError):
                    continue
                days.setdefault(day, {})[code] = _number(entry.findtext('Value'))
        if not days:
            raise self._no_rates()
        day = max(days)
        return day, self.home_currency, self._from_home_quotes(days[day])


class CbaReader(CentralBankReader):
    """ The official exchange rates of the Central Bank of Armenia, in AMD per amount (1, 10, 100... units), for
    about 40 currencies, from its public web service (SOAP). """
    code = 'cba'
    name = 'Central Bank of Armenia'
    country = 'AM'
    country_name = 'Armenia'
    home_currency = 'AMD'
    url = 'https://api.cba.am/exchangerates.asmx'
    headers = dict(CentralBankReader.headers, **{
        'Content-Type': 'text/xml; charset=utf-8', 'SOAPAction': '"http://www.cba.am/ExchangeRatesLatest"'})
    envelope = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        '<soap:Body><ExchangeRatesLatest xmlns="http://www.cba.am/"/></soap:Body></soap:Envelope>')

    def fetch(self):
        try:
            root = etree.fromstring(self._request('post', self.url, data=self.envelope.encode()).content)
            # "2026-10-30T00:00:00"
            day = date.fromisoformat((root.findtext('.//{*}CurrentDate') or '')[:10])
        except (etree.XMLSyntaxError, ValueError) as error:
            raise self._no_rates() from error
        quotes, units = {}, {}
        for rate in root.iter('{*}ExchangeRate'):
            code = rate.findtext('{*}ISO')
            quotes[code], units[code] = _number(rate.findtext('{*}Rate')), _number(rate.findtext('{*}Amount')) or 1
        if not quotes:
            raise self._no_rates()
        return day, self.home_currency, self._from_home_quotes(quotes, units)


class NbrbReader(CentralBankReader):
    """ The official exchange rates of the National Bank of the Republic of Belarus, in BYN per scale (1, 10,
    100... units), for about 30 currencies, set each working day for the next day, from its API. """
    code = 'nbrb'
    name = 'National Bank of the Republic of Belarus'
    country = 'BY'
    country_name = 'Belarus'
    home_currency = 'BYN'
    decimals = 4
    url = 'https://api.nbrb.by/exrates/rates'

    def fetch(self):
        # the daily rates
        data = self._get_data('get', self.url, params={'periodicity': 0})
        items = [item for item in (data if isinstance(data, list) else [])
                 if isinstance(item, dict) and item.get('Cur_Abbreviation') and item.get('Date')]
        if not items:
            raise self._no_rates()
        # "2026-10-31T00:00:00": the day the rates apply from
        day = max(item['Date'][:10] for item in items)
        quotes = {item['Cur_Abbreviation']: item.get('Cur_OfficialRate') for item in items}
        units = {item['Cur_Abbreviation']: item.get('Cur_Scale') or 1 for item in items}
        return date.fromisoformat(day), self.home_currency, self._from_home_quotes(quotes, units)


# Americas and Asia-Pacific

class BocReader(CentralBankReader):
    """ The daily exchange rates of the Bank of Canada, in CAD per 1 unit, for about 25 currencies, published each
    business day by 4:30 PM (Eastern), from its Valet API. """
    code = 'boc'
    name = 'Bank of Canada'
    country = 'CA'
    country_name = 'Canada'
    home_currency = 'CAD'
    decimals = 6
    url = 'https://www.bankofcanada.ca/valet/observations/group/FX_RATES_DAILY/json'

    def fetch(self):
        data = self._get_data('get', self.url, params={'recent': 1})
        # the newest observation of each series: the series no longer published stop at an older day
        observations = [item for item in (data.get('observations') if isinstance(data, dict) else None) or []
                        if isinstance(item, dict) and item.get('d')]
        if not observations:
            raise self._no_rates()
        day = max(item['d'] for item in observations)
        quotes = {}
        for item in observations:
            if item['d'] == day:
                quotes.update({series[2:5]: _number(value.get('v')) for series, value in item.items()
                               if re.fullmatch(r'FX[A-Z]{3}CAD', series) and isinstance(value, dict)})
        return date.fromisoformat(day), self.home_currency, self._from_home_quotes(quotes)


class BcbReader(CentralBankReader):
    """ The PTAX closing rates of the Banco Central do Brasil, in BRL per 1 unit, for about 150 currencies,
    published each business day around 1:10 PM (Brasília) in a file by day. Only buying and selling rates are
    published: the mid rate is used. """
    code = 'bcb'
    name = 'Banco Central do Brasil (PTAX)'
    country = 'BR'
    country_name = 'Brazil'
    home_currency = 'BRL'
    url = 'https://www4.bcb.gov.br/Download/fechamento/%s.csv'
    days = 7  # the days looked back, covering the holidays

    def fetch(self):
        today = date.today()
        for day in (today - timedelta(days=days) for days in range(self.days)):
            try:
                response = requests.get(self.url % day.strftime('%Y%m%d'), timeout=TIMEOUT, headers=self.headers)
                if response.status_code == 404:
                    # no file for the days without rates, nor for today before the closing
                    continue
                response.raise_for_status()
            except requests.RequestException as error:
                raise UserError(self.company.env._(
                    '%(provider)s could not be reached: %(error)s', provider=self.name, error=error)) from error
            break
        else:
            raise self._no_rates()
        quotes = {}
        # 30/10/2026;220;A;USD;5,42060000;5,42120000;1,00000000;1,00000000
        for line in response.content.decode('latin-1').splitlines():
            cells = line.split(';')
            if len(cells) >= 6 and re.fullmatch(r'[A-Z]{3}', cells[3]):
                buying, selling = (_number(cell.replace(',', '.')) for cell in cells[4:6])
                if buying and selling:
                    quotes[cells[3]] = (buying + selling) / 2
        if not quotes:
            raise self._no_rates()
        return day, self.home_currency, self._from_home_quotes(quotes)


class BnmReader(CentralBankReader):
    """ The exchange rates of Bank Negara Malaysia (5 PM session), in MYR per 1 unit (or per 100), for about 25
    currencies, from its open API. """
    code = 'bnm'
    name = 'Bank Negara Malaysia'
    country = 'MY'
    country_name = 'Malaysia'
    home_currency = 'MYR'
    decimals = 4
    url = 'https://api.bnm.gov.my/public/exchange-rate'
    headers = dict(CentralBankReader.headers, Accept='application/vnd.BNM.API.v1+json')
    aliases = {'SDR': 'XDR'}

    def fetch(self):
        data = self._get_data('get', self.url)
        items = [item for item in (data.get('data') if isinstance(data, dict) else None) or []
                 if isinstance(item, dict) and item.get('currency_code') and (item.get('rate') or {}).get('date')]
        if not items:
            raise self._no_rates()
        day = max(item['rate']['date'] for item in items)
        quotes, units = {}, {}
        for item in items:
            if item['rate']['date'] == day:
                code = self.aliases.get(item['currency_code'], item['currency_code'])
                quotes[code], units[code] = item['rate'].get('middle_rate'), item.get('unit') or 1
        return date.fromisoformat(day), self.home_currency, self._from_home_quotes(quotes, units)


class BspReader(CentralBankReader):
    """ The reference exchange rates of the Bangko Sentral ng Pilipinas, in PHP per 1 unit, for about 30
    currencies, from the list its exchange rates page loads. """
    code = 'bsp'
    name = 'Bangko Sentral ng Pilipinas'
    country = 'PH'
    country_name = 'Philippines'
    home_currency = 'PHP'
    decimals = 4
    url = "https://www.bsp.gov.ph/_api/web/lists/getByTitle('Exchange Rate')/items"
    # unlike the others, its firewall refuses most user agents but the default one of requests
    headers = {'Accept': 'application/json;odata=nometadata'}

    def fetch(self):
        data = self._get_data('get', self.url, params={
            '$select': 'Symbol,Group,PHPequivalent,PublishedDate', '$orderby': 'Ordering', '$top': 200})
        # the currencies are in the groups 1 and 2; then the rates of the peso itself, gold, the notes
        items = [item for item in (data.get('value') if isinstance(data, dict) else None) or []
                 if isinstance(item, dict) and item.get('Group') in ('1', '2') and item.get('PublishedDate')
                 and re.fullmatch(r'[A-Z]{3}', item.get('Symbol') or '')]
        if not items:
            raise self._no_rates()
        # "2026-10-29T16:00:00Z": midnight in Manila of the day of the bulletin
        published = max(datetime.fromisoformat(item['PublishedDate'].replace('Z', '+00:00')) for item in items)
        day = (published + timedelta(hours=8)).date()
        quotes = {item['Symbol']: _number(item.get('PHPequivalent')) for item in items}
        return day, self.home_currency, self._from_home_quotes(quotes)


class RbaReader(CentralBankReader):
    """ The exchange rates of the Reserve Bank of Australia at 4 PM (Sydney), in units of about 20 currencies per
    1 AUD, from its RSS feed. """
    code = 'rba'
    name = 'Reserve Bank of Australia'
    country = 'AU'
    country_name = 'Australia'
    home_currency = 'AUD'
    decimals = 4
    url = 'https://www.rba.gov.au/rss/rss-cb-exchange-rates.xml'
    # like the BSP, its firewall refuses the user agents but the default one of requests
    headers = {}

    def fetch(self):
        try:
            root = etree.fromstring(self._request('get', self.url).content)
        except etree.XMLSyntaxError as error:
            raise self._no_rates() from error
        days = {}
        for rate in root.iter('{*}exchangeRate'):
            # 0.7040 USD for 1 AUD on 2026-10-30; XXX is the trade-weighted index
            code, day = rate.findtext('{*}targetCurrency'), rate.findtext('.//{*}period')
            if rate.findtext('{*}baseCurrency') == 'AUD' and day and re.fullmatch(r'[A-Z]{3}', code or '') \
                    and code != 'XXX':
                days.setdefault(day, {})[code] = _number(rate.findtext('.//{*}value'))
        if not days:
            raise self._no_rates()
        day = max(days)
        return date.fromisoformat(day), self.home_currency, self._from_home_rates(days[day])


class MasReader(CentralBankReader):
    """ The exchange rates published by the Monetary Authority of Singapore, the average of the buying and selling
    interbank rates around noon (Singapore), in SGD per 1 unit (per 100 for most), for 21 currencies, from the
    daily table of its statistics form, posted for the last days with every currency. """
    code = 'mas'
    name = 'Monetary Authority of Singapore'
    country = 'SG'
    country_name = 'Singapore'
    home_currency = 'SGD'
    url = 'https://eservices.mas.gov.sg/statistics/msb/exchangerates.aspx'
    days = 10  # the period asked, covering the holidays
    field = 'ctl00$ContentPlaceHolder1$%s'
    currencies = {
        'euro': 'EUR', 'pound sterling': 'GBP', 'us dollar': 'USD', 'australian dollar': 'AUD',
        'canadian dollar': 'CAD', 'chinese renminbi': 'CNY', 'hong kong dollar': 'HKD', 'indian rupee': 'INR',
        'indonesian rupiah': 'IDR', 'japanese yen': 'JPY', 'korean won': 'KRW', 'malaysian ringgit': 'MYR',
        'new taiwan dollar': 'TWD', 'new zealand dollar': 'NZD', 'philippine peso': 'PHP', 'qatar riyal': 'QAR',
        'saudi arabia riyal': 'SAR', 'swiss franc': 'CHF', 'thai baht': 'THB', 'uae dirham': 'AED',
        'vietnamese dong': 'VND',
    }

    def fetch(self):
        form = self._get_page(self.url)
        data = {node.get('name'): node.get('value') or '' for node in form.xpath('//input[@type="hidden"][@name]')}
        data.update({node.get('name'): 'on' for node in form.xpath('//input[@type="checkbox"][@name]')})
        today = date.today()
        start = today - timedelta(days=self.days)
        data.update({
            self.field % 'StartYearDropDownList': start.year, self.field % 'StartMonthDropDownList': start.month,
            self.field % 'EndYearDropDownList': today.year, self.field % 'EndMonthDropDownList': today.month,
            self.field % 'FrequencyDropDownList': 'D', self.field % 'DisplayButton': 'Display',
        })
        page = html.fromstring(self._request('post', self.url, data=data).content)
        table = page.xpath('//table[thead//th[contains(., "Units of")] or thead//th[contains(., "Unit of")]]')
        if not table:
            raise self._no_rates()
        # "End of Period" over 3 columns, then "S$ Per 100 Units of Japanese Yen"
        columns = []
        for cell in table[0].xpath('./thead//th'):
            match = re.search(r'Per\s+(\d*)\s*Units?\s+of\s+(.+)', ' '.join(' '.join(cell.itertext()).split()))
            columns.append(match and (self.currencies.get(match.group(2).lower()), int(match.group(1) or 1)))
        # the year and the month are written on the first row of each
        days, year, month = {}, None, None
        for row in table[0].xpath('./tbody/tr'):
            cells = [cell.text_content().strip() for cell in row]
            if len(cells) != len(columns) + 2:
                continue
            year = int(cells[0]) if cells[0].isdigit() else year
            month = _month(cells[1]) or month
            if not (year and month and cells[2].isdigit()):
                continue
            days[date(year, month, int(cells[2]))] = {
                column: _number(value) for column, value in zip(columns[1:], cells[3:], strict=False)
                if column and column[0]}
        if not days:
            raise self._no_rates()
        day = max(days)
        quotes = {code: value for (code, unit), value in days[day].items()}
        units = {code: unit for code, unit in days[day]}
        return day, self.home_currency, self._from_home_quotes(quotes, units)


class BanrepReader(CentralBankReader):
    """ The TRM (tasa representativa del mercado) of the Colombian peso, in COP per 1 US dollar, certified each
    working day by the Superintendencia Financiera and published by the Banco de la República; read from the
    open data portal of the government of Colombia. """
    code = 'banrep'
    name = 'Banco de la República (TRM)'
    country = 'CO'
    country_name = 'Colombia'
    home_currency = 'COP'
    decimals = 2
    url = 'https://www.datos.gov.co/resource/32sa-8pi3.json'

    def fetch(self):
        data = self._get_data('get', self.url, params={'$order': 'vigenciadesde DESC', '$limit': 1})
        # {"valor": "3182.99", "unidad": "COP", "vigenciadesde": "2026-10-31T00:00:00.000", ...}
        item = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else {}
        if item.get('unidad') != self.home_currency or not item.get('vigenciadesde') or not _number(item.get('valor')):
            raise self._no_rates()
        # the day the rate applies from: the TRM of the weekend and of Monday is set on Friday
        day = date.fromisoformat(item['vigenciadesde'][:10])
        return day, self.home_currency, self._from_home_quotes({'USD': _number(item['valor'])})


class BcraReader(CentralBankReader):
    """ The closing exchange rates of the Banco Central de la República Argentina, in ARS per 1 unit, for about 35
    currencies, from its open API of exchange statistics. """
    code = 'bcra'
    name = 'Banco Central de la República Argentina'
    country = 'AR'
    country_name = 'Argentina'
    home_currency = 'ARS'
    url = 'https://api.bcra.gob.ar/estadisticascambiarias/v1.0/Cotizaciones'
    # MXP is the old code of the Mexican peso; REF, the reference rate of the US dollar (Communication A 3500),
    # is not a currency
    aliases = {'MXP': 'MXN'}

    def fetch(self):
        data = self._get_data('get', self.url)
        results = (data.get('results') if isinstance(data, dict) else None) or {}
        items = [item for item in (results.get('detalle') if isinstance(results, dict) else None) or []
                 if isinstance(item, dict) and re.fullmatch(r'[A-Z]{3}', item.get('codigoMoneda') or '')]
        if not results.get('fecha') or not items:
            raise self._no_rates()
        quotes, units = {}, {}
        for item in items:
            code = self.aliases.get(item['codigoMoneda'], item['codigoMoneda'])
            quotes[code] = item.get('tipoCotizacion')
            # "DONG VIETNAM (C/1.000 UNIDADES)"
            unit = re.search(r'C/\s*([\d.]+)\s*UNIDADES', item.get('descripcion') or '')
            units[code] = int(unit.group(1).replace('.', '')) if unit else 1
        quotes.pop('REF', None)
        return date.fromisoformat(results['fecha']), self.home_currency, self._from_home_quotes(quotes, units)


CENTRAL_BANKS = {bank.code: bank for bank in (
    RbiReader, SamaReader, CbuaeReader, CboReader, CbkKuwaitReader, CbbReader, CbjReader, BoiReader,
    BangladeshBankReader, CbnReader, CbkKenyaReader, CbslReader, TcmbReader, NbpReader, CnbReader, BnrReader,
    MnbReader, NbuReader, NbgReader, NbkReader, BoeReader, SnbReader, NorgesBankReader, RiksbankReader,
    DanmarksNationalbankReader, SedlabankiReader, CbaReader, NbrbReader, BocReader, BcbReader, BnmReader, BspReader,
    RbaReader, MasReader, BanrepReader, BcraReader,
)}

PROVIDERS = {provider.code: provider for provider in (
    EcbProvider, FrankfurterProvider, OpenExchangeRatesProvider, ExchangeRateApiProvider, CentralBankProvider,
)}
