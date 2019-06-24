# -*- coding: utf-8 -*-
"""
Convert currency rate based on company currency by using xe.com platform
"""
import requests
from lxml import etree
from odoo import api, fields, models
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    """List out the service provider for exchange the currency rate based on our company currency"""
    _inherit = 'res.config.settings'

    currency_update = fields.Boolean(string='Live Currency Rate Update')
    service_provider = fields.Selection(related="company_id.service_provider", readonly=False)

    @api.model
    def get_values(self):
        """get values from the fields"""
        res = super(ResConfigSettings, self).get_values()
        res.update(
            currency_update=self.env['ir.config_parameter'].sudo().get_param('currency_update'),
            service_provider=self.env['ir.config_parameter'].sudo().get_param('service_provider')
        )
        return res

    @api.multi
    def set_values(self):
        """Set values in the fields"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('service_provider', self.service_provider)
        self.env['ir.config_parameter'].sudo().set_param('currency_update', self.currency_update)

    def update_rate(self):
        """Update the currency rate manually"""
        self.ensure_one()
        if self.company_id.service_provider != 'xe_com':
            raise UserError("Please select a service provider. ")

        if not (self.company_id.currency_rate_updates()):
            raise UserError('Unable to connect at this this time.'
                            'Please try again later.')


class ResCompany(models.Model):
    """This class generate the current currency rate from xe.com website"""
    _inherit = 'res.company'

    service_provider = fields.Selection([
        ('xe_com', 'xe.com'),
    ], string='Service', default='xe_com')

    @api.multi
    def currency_rate_updates(self):
        """This method is used to update all currencies given by the provider."""
        result = True
        active_currencies = self.env['res.currency'].search([])
        for (service_provider, companies) in self.currency_provider().items():
            results = None
            if service_provider == 'xe_com':
                function = getattr(companies, service_provider + '_data')
                results = function(active_currencies)
            if service_provider != 'xe_com':
                raise UserError("Unavailable currency rate web service.")
            else:
                companies.res_currency_rate(results)

        return result

    def currency_provider(self):
        """Returns a dictionary the companies in self by currency
        rate provider."""
        result = {}
        for company in self:
            if not company.service_provider:
                continue
            else:
                result[company.service_provider] = company
        return result

    def res_currency_rate(self, data):
        """Generate the entries of currency rates for the company,
        using the result of a function, given as parameter, to get the rates data."""
        res_currency = self.env['res.currency']
        currency_rate = self.env['res.currency.rate']
        for company in self:
            currency_rate_info = data.get(company.currency_id.name, None)
            if not currency_rate_info:
                raise UserError(("Main currency %s is not supported by this service provider. "
                                 "Choose another one.") % company.currency_id.name)

            base_currency = currency_rate_info[0]
            for currency, (rate, date_rate) in data.items():
                value = rate/base_currency
                currency_object = res_currency.search([('name', '=', currency)])
                existing_rate = currency_rate.search([('currency_id', '=', currency_object.id),
                                                      ('name', '=', date_rate),
                                                      ('company_id', '=', company.id)])
                if existing_rate:
                    existing_rate.rate = value
                else:
                    currency_rate.create({'currency_id': currency_object.id,
                                          'rate': value,
                                          'name': date_rate,
                                          'company_id': company.id})

    def xe_com_data(self, currencies):
        """Import the currency rates data from the xe.com service provider.
        As this provider does not have an API, here we directly extract exchange rate
        from HTML."""

        url = 'http://www.xe.com/currencytables/?from=%(currency_code)s&date=%(date)s'
        today = fields.Date.today()
        data = requests.request('GET', url % {'currency_code': 'INR', 'date': today})
        result = {}
        available_currencies = currencies.mapped('name')
        html_content = etree.fromstring(data.content, etree.HTMLParser())
        table_rate = html_content.find(".//table[@id='historicalRateTbl']/tbody")
        for table_entry in list(table_rate):
            if type(
                    table_entry) != etree._Comment:
                code = table_entry.find('.//a').text
                if code in available_currencies:
                    rate = float(table_entry.find(
                        "td[@class='historicalRateTable-rateHeader']").text)
                    result[code] = (rate, today)
        return result

    @api.model
    def cron_update(self):
        """Update currency rate automatically by using cron job"""
        update_company = self.env['res.company'].search([])
        update_company.currency_rate_updates()
