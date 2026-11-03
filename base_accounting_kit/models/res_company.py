# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
import calendar
import logging
import math
import re
from datetime import datetime, date, timezone, timedelta
from xml.etree import ElementTree as ET
from lxml import html
from dateutil.relativedelta import relativedelta
import requests

from odoo import fields, models, api, _
from odoo.exceptions import UserError, RedirectWarning

_logger = logging.getLogger(__name__)

SYNC_TIMEOUT = 15

from .rate_providers import CENTRAL_BANKS

CENTRAL_BANK_SELECTION = sorted(
    ((bank.code, '%s - %s' % (bank.country_name, bank.name)) for bank in CENTRAL_BANKS.values()),
    key=lambda item: item[1])


class ResCompany(models.Model):
    """Model for inheriting res_company."""
    _inherit = "res.company"

    fx_reval_journal_id = fields.Many2one(
        'account.journal', string='FX Revaluation Journal',
        domain="[('type', '=', 'general'), ('company_id', '=', id)]",
        help="Journal used for foreign-currency revaluation entries.")
    fx_reval_gain_account_id = fields.Many2one(
        'account.account', string='Unrealized FX Gain Account',
        help="Account crediting the unrealized foreign-exchange gains.")
    fx_reval_loss_account_id = fields.Many2one(
        'account.account', string='Unrealized FX Loss Account',
        help="Account debiting the unrealized foreign-exchange losses.")

    currency_provider = fields.Selection([
        ('frankfurter', 'Frankfurter (ECB Rates)'),
        ('ecb', 'European Central Bank'),
        ('exchangerate_api', 'ExchangeRate-API (160+ Currencies)'),
        ('openexchangerates', 'Open Exchange Rates (170+ Currencies & Metals)'),
        ('central_bank', 'Central Bank (Official Rates)'),
    ], string='Currency Rates Provider', default='frankfurter',
       help="Service provider used to synchronize foreign currency exchange rates.")
    currency_central_bank = fields.Selection(
        CENTRAL_BANK_SELECTION, string='Central Bank', default='boc',
        help="Select the national central bank to fetch official government rates from.")
    currency_rate_interval = fields.Selection([
        ('manual', 'Manually'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Currency Sync Interval', default='daily',
       help="Interval between automated currency rate synchronizations.")
    currency_api_key = fields.Char(
        string='Provider API Key',
        help="Optional API key for services that require authentication.")
    currency_last_sync_date = fields.Datetime(
        string='Last Currency Sync', readonly=True,
        help="Timestamp of the most recent exchange rate synchronization.")
    currency_next_sync_date = fields.Date(
        string='Next Currency Sync',
        help="Date when the next currency rate synchronization is scheduled.")
    currency_max_change = fields.Float(
        string='Hold Back Changes Above (%)', default=20.0,
        help="Maximum allowed percentage change compared to the latest recorded rate before the rate "
             "update is held back as a potential anomaly. Set to 0 to save all rates.")

    def _fetch_rates_from_frankfurter(self):
        """Fetch latest exchange rates from the Frankfurter open REST API."""
        url = "https://api.frankfurter.dev/v1/latest"
        try:
            response = requests.get(url, timeout=SYNC_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            base = data.get('base', 'EUR')
            rates = data.get('rates', {})
            rates[base] = 1.0
            rate_date = data.get('date', fields.Date.today().isoformat())
            return base, rates, rate_date
        except Exception as err:
            _logger.warning("Frankfurter rate fetch failed: %s", err)
            raise UserError(_("Could not fetch rates from Frankfurter: %s") % err)

    def _fetch_rates_from_ecb(self):
        """Fetch latest exchange rates from the official European Central Bank XML feed."""
        url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
        try:
            response = requests.get(url, timeout=SYNC_TIMEOUT)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            rates = {'EUR': 1.0}
            rate_date = fields.Date.today().isoformat()
            for cube in root.iter('{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube'):
                if 'time' in cube.attrib:
                    rate_date = cube.attrib['time']
                if 'currency' in cube.attrib and 'rate' in cube.attrib:
                    try:
                        rates[cube.attrib['currency']] = float(cube.attrib['rate'])
                    except ValueError:
                        continue
            return 'EUR', rates, rate_date
        except Exception as err:
            _logger.warning("ECB rate fetch failed: %s", err)
            raise UserError(_("Could not fetch rates from European Central Bank: %s") % err)

    def _fetch_rates_from_exchangerate_api(self):
        """Fetch latest exchange rates from ExchangeRate-API (160+ currencies)."""
        if self.currency_api_key:
            url = f"https://v6.exchangerate-api.com/v6/{self.currency_api_key}/latest/USD"
        else:
            url = "https://open.er-api.com/v6/latest/USD"
        try:
            response = requests.get(url, timeout=SYNC_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if data.get('result') == 'error':
                raise UserError(_("ExchangeRate-API error: %s") % data.get('error-type', 'Unknown error'))
            base = data.get('base_code', 'USD')
            rates = data.get('rates', {})
            rate_date = fields.Date.today().isoformat()
            return base, rates, rate_date
        except Exception as err:
            _logger.warning("ExchangeRate-API fetch failed: %s", err)
            raise UserError(_("Could not fetch rates from ExchangeRate-API: %s") % err)

    def _fetch_rates_from_openexchangerates(self):
        """Fetch latest exchange rates from Open Exchange Rates API."""
        if not self.currency_api_key:
            raise UserError(_("Please configure the App ID for Open Exchange Rates in Accounting Settings."))
        url = "https://openexchangerates.org/api/latest.json"
        try:
            response = requests.get(url, params={'app_id': self.currency_api_key}, timeout=SYNC_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if data.get('error'):
                raise UserError(_("Open Exchange Rates error: %s") % (data.get('description') or data.get('message') or data))
            rates = data.get('rates', {})
            base = data.get('base', 'USD')
            timestamp = data.get('timestamp')
            if timestamp:
                rate_date = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
            else:
                rate_date = fields.Date.today().isoformat()
            return base, rates, rate_date
        except requests.RequestException as err:
            _logger.warning("Open Exchange Rates fetch failed: %s", err)
            raise UserError(_("Could not fetch rates from Open Exchange Rates: %s") % err)

    def _fetch_rates_from_central_bank(self):
        """Fetch latest official exchange rates from the selected national central bank."""
        bank_code = self.currency_central_bank or 'boc'
        bank_class = CENTRAL_BANKS.get(bank_code)
        if not bank_class:
            raise UserError(_("Selected Central Bank is not available: %s") % bank_code)
        bank_reader = bank_class(self)
        rate_date, source_base, raw_rates = bank_reader.fetch()
        rate_date_str = rate_date.isoformat() if hasattr(rate_date, 'isoformat') else str(rate_date)
        return source_base, raw_rates, rate_date_str

    def action_update_currency_rates(self):
        """Fetch live currency exchange rates and update Odoo's currency rate table."""
        self.ensure_one()
        provider = self.currency_provider or 'frankfurter'

        if provider == 'frankfurter':
            source_base, raw_rates, rate_date_str = self._fetch_rates_from_frankfurter()
        elif provider == 'ecb':
            source_base, raw_rates, rate_date_str = self._fetch_rates_from_ecb()
        elif provider == 'exchangerate_api':
            source_base, raw_rates, rate_date_str = self._fetch_rates_from_exchangerate_api()
        elif provider == 'openexchangerates':
            source_base, raw_rates, rate_date_str = self._fetch_rates_from_openexchangerates()
        elif provider == 'central_bank':
            source_base, raw_rates, rate_date_str = self._fetch_rates_from_central_bank()
        else:
            raise UserError(_("Unsupported currency rate provider: %s") % provider)

        company_currency = self.currency_id.name
        if not company_currency:
            raise UserError(_("Please configure the main currency for your company first."))

        if company_currency not in raw_rates and company_currency != source_base:
            raise UserError(_(
                "The selected provider '%s' does not quote your company base currency (%s)."
            ) % (provider, company_currency))

        company_unit_in_source = raw_rates.get(company_currency, 1.0)
        if not isinstance(company_unit_in_source, (int, float)) or not math.isfinite(company_unit_in_source) or company_unit_in_source <= 0:
            raise UserError(_("Invalid rate value received for company currency %s") % company_currency)

        rate_date = fields.Date.from_string(rate_date_str) or fields.Date.today()
        currencies = self.env['res.currency'].search([('active', '=', True)])
        RateModel = self.env['res.currency.rate']
        updated_count = 0
        updated_currencies = []
        skipped_currencies = []

        for curr in currencies:
            if curr.name == company_currency:
                continue
            if curr.name in raw_rates:
                target_unit_in_source = raw_rates[curr.name]
                if not isinstance(target_unit_in_source, (int, float)) or not math.isfinite(target_unit_in_source) or target_unit_in_source <= 0:
                    _logger.warning("Invalid raw rate received for %s: %s", curr.name, target_unit_in_source)
                    continue

                calculated_rate = target_unit_in_source / company_unit_in_source
                if not math.isfinite(calculated_rate) or calculated_rate <= 0:
                    continue

                # Spike protection: check against previous recorded rate for this company
                if self.currency_max_change > 0:
                    prev_rate_rec = RateModel.search([
                        ('currency_id', '=', curr.id),
                        ('company_id', '=', self.id),
                        ('name', '<', rate_date),
                    ], order='name desc, id desc', limit=1)
                    if not prev_rate_rec:
                        prev_rate_rec = RateModel.search([
                            ('currency_id', '=', curr.id),
                            ('company_id', '=', False),
                            ('name', '<', rate_date),
                        ], order='name desc, id desc', limit=1)

                    if prev_rate_rec and prev_rate_rec.rate and prev_rate_rec.rate > 0:
                        change_pct = abs(calculated_rate - prev_rate_rec.rate) / prev_rate_rec.rate * 100.0
                        if change_pct > self.currency_max_change:
                            _logger.warning(
                                "Currency rate spike detected for %s in company '%s': "
                                "new rate %.6f differs from previous rate %.6f by %.2f%% (threshold %.2f%%). Skipped.",
                                curr.name, self.name, calculated_rate, prev_rate_rec.rate, change_pct, self.currency_max_change
                            )
                            skipped_currencies.append((curr.name, prev_rate_rec.rate, calculated_rate, change_pct))
                            continue

                existing_rate = RateModel.search([
                    ('currency_id', '=', curr.id),
                    ('company_id', '=', self.id),
                    ('name', '=', rate_date),
                ], limit=1)

                if existing_rate:
                    existing_rate.write({'rate': calculated_rate})
                else:
                    RateModel.create({
                        'currency_id': curr.id,
                        'company_id': self.id,
                        'name': rate_date,
                        'rate': calculated_rate,
                    })
                updated_currencies.append(f"{curr.name} ({calculated_rate:.4g})")

        now = fields.Datetime.now()
        today = fields.Date.today()
        vals = {'currency_last_sync_date': now}
        interval = self.currency_rate_interval or 'daily'
        if interval == 'daily':
            vals['currency_next_sync_date'] = today + relativedelta(days=1)
        elif interval == 'weekly':
            vals['currency_next_sync_date'] = today + relativedelta(weeks=1)
        elif interval == 'monthly':
            vals['currency_next_sync_date'] = today + relativedelta(months=1)
        self.write(vals)

        updated_count = len(updated_currencies)
        if updated_count > 0:
            msg_parts = [_('Successfully updated %d currency rate(s) for %s: %s') % (
                updated_count, rate_date, ', '.join(updated_currencies)
            )]
        else:
            msg_parts = [_('No currency rates updated for %s.') % rate_date]

        notification_type = 'success'
        if skipped_currencies:
            skipped_details = [
                f"{s[0]} ({s[1]:.4g} → {s[2]:.4g}, +{s[3]:.1f}%)"
                for s in skipped_currencies
            ]
            msg_parts.append(
                _('Held back %d rate(s) exceeding max allowed change (%.1f%%): %s') %
                (len(skipped_currencies), self.currency_max_change, '; '.join(skipped_details))
            )
            if updated_count == 0:
                notification_type = 'warning'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Currency Rates Updated') if updated_count > 0 else _('Currency Rates Warning'),
                'message': '\n'.join(msg_parts),
                'type': notification_type,
                'sticky': bool(skipped_currencies),
            }
        }

    @api.model
    def _cron_update_all_company_currency_rates(self):
        """Cron task to automatically update currency rates for companies on schedule."""
        today = fields.Date.today()
        companies = self.search([
            ('currency_rate_interval', '!=', 'manual'),
            '|',
            ('currency_next_sync_date', '<=', today),
            ('currency_next_sync_date', '=', False),
        ])
        for company in companies:
            try:
                with self.env.cr.savepoint():
                    company.action_update_currency_rates()
            except Exception as err:
                _logger.error("Failed to auto-update currency rates for company '%s': %s", company.name, err)

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure fiscal year day does not exceed the maximum valid day for the selected month during record creation."""
        for vals in vals_list:
            if 'fiscalyear_last_month' in vals and 'fiscalyear_last_day' in vals:
                month = vals.get('fiscalyear_last_month')
                day = vals.get('fiscalyear_last_day')
                if month and day:
                    opening_date = vals.get('account_opening_date')
                    if opening_date:
                        year = fields.Date.to_date(opening_date).year
                    else:
                        year = datetime.now().year
                    max_day = calendar.monthrange(year, int(month))[1]
                    if int(day) > max_day:
                        vals['fiscalyear_last_day'] = max_day
        return super().create(vals_list)

    def write(self, vals):
        """Auto-correct fiscal year day to a valid value when month or day is updated to prevent invalid calendar dates."""
        if 'fiscalyear_last_month' in vals or 'fiscalyear_last_day' in vals:
            month = vals.get('fiscalyear_last_month')
            day = vals.get('fiscalyear_last_day')
            if month:
                if self.account_opening_date:
                    year = self.account_opening_date.year
                else:
                    year = datetime.now().year
                max_day = calendar.monthrange(year, int(month))[1]
                if not day:
                    if any(company.fiscalyear_last_day > max_day for company in self):
                        vals['fiscalyear_last_day'] = max_day
                elif int(day) > max_day:
                    vals['fiscalyear_last_day'] = max_day

        return super().write(vals)

    def _get_unreconciled_statement_lines_redirect_action(self, unreconciled_statement_lines):
        """Ensure 'views' is explicitly populated to avoid web client TypeError
        and redirect to the custom bank reconciliation widget."""
        action = super()._get_unreconciled_statement_lines_redirect_action(unreconciled_statement_lines)
        kanban_view = self.env.ref(
            'base_accounting_kit.account_bank_statement_line_view_kanban',
            raise_if_not_found=False
        )
        kanban_id = kanban_view.id if kanban_view else False

        if len(unreconciled_statement_lines) == 1:
            action['views'] = [(False, 'form')]
        else:
            action['view_mode'] = 'kanban,list,form'
            action['views'] = [(kanban_id, 'kanban'), (False, 'list'), (False, 'form')]

        return action
