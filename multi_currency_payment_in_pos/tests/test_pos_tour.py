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
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon


@tagged('post_install', '-at_install')
class TestPosMulticurrencyTour(TestPointOfSaleHttpCommon):
    """Tour test verifying payment screen multi-currency payment flow."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env(su=True)
        currency_eur = env.ref('base.EUR', raise_if_not_found=False)
        if not currency_eur:
            currency_eur = env['res.currency'].create({
                'name': 'EUR',
                'symbol': '€',
                'active': True,
            })
        else:
            currency_eur.write({'active': True})

        currency_usd = env.ref('base.USD', raise_if_not_found=False)
        if not currency_usd:
            currency_usd = env['res.currency'].create({
                'name': 'USD',
                'symbol': '$',
                'active': True,
            })
        else:
            currency_usd.write({'active': True})

        # Update any existing rates for EUR and USD to match test rates
        all_eur_rates = env['res.currency.rate'].search([('currency_id', '=', currency_eur.id)])
        if all_eur_rates:
            all_eur_rates.write({'rate': 1.1})
        all_usd_rates = env['res.currency.rate'].search([('currency_id', '=', currency_usd.id)])
        if all_usd_rates:
            all_usd_rates.write({'rate': 1.0})

        target_companies = env['res.company'].search([]) | cls.main_pos_config.company_id | cls.env.company
        for comp in target_companies:
            rate_eur = env['res.currency.rate'].search([
                ('currency_id', '=', currency_eur.id),
                ('company_id', '=', comp.id),
            ], limit=1)
            if rate_eur:
                rate_eur.write({'rate': 1.1})
            else:
                env['res.currency.rate'].create({
                    'currency_id': currency_eur.id,
                    'rate': 1.1,
                    'name': '2010-01-01',
                    'company_id': comp.id,
                })

            rate_usd = env['res.currency.rate'].search([
                ('currency_id', '=', currency_usd.id),
                ('company_id', '=', comp.id),
            ], limit=1)
            if rate_usd:
                rate_usd.write({'rate': 1.0})
            else:
                env['res.currency.rate'].create({
                    'currency_id': currency_usd.id,
                    'rate': 1.0,
                    'name': '2010-01-01',
                    'company_id': comp.id,
                })

        no_comp_rates = env['res.currency.rate'].search([
            ('currency_id', 'in', [currency_eur.id, currency_usd.id]),
            ('company_id', '=', False),
        ])
        for r in no_comp_rates:
            if r.currency_id.id == currency_eur.id:
                r.write({'rate': 1.1})
            elif r.currency_id.id == currency_usd.id:
                r.write({'rate': 1.0})

        env.cr.cache.clear()
        env['res.currency'].invalidate_model()
        env['res.currency.rate'].invalidate_model()

        bank_pm = cls.main_pos_config.payment_method_ids.filtered(lambda pm: pm.type == 'bank')
        cash_pm = cls.main_pos_config.payment_method_ids.filtered(lambda pm: pm.type == 'cash')
        if not cash_pm:
            cash_journal = env['account.journal'].create({
                'name': 'Cash MultiCurrency Test',
                'type': 'cash',
                'company_id': cls.main_pos_config.company_id.id,
                'code': 'CSHM',
            })
            cash_pm = env['pos.payment.method'].create({
                'name': 'Cash',
                'type': 'cash',
                'journal_id': cash_journal.id,
                'receivable_account_id': cls.account_receivable.id,
                'company_id': cls.main_pos_config.company_id.id,
            })
        if not bank_pm:
            bank_journal = env['account.journal'].create({
                'name': 'Bank MultiCurrency Test',
                'type': 'bank',
                'company_id': cls.main_pos_config.company_id.id,
                'code': 'BNKM',
            })
            bank_pm = env['pos.payment.method'].create({
                'name': 'Bank',
                'type': 'bank',
                'journal_id': bank_journal.id,
                'receivable_account_id': cls.account_receivable.id,
                'company_id': cls.main_pos_config.company_id.id,
            })
        bank_pm[0].sequence = 1
        cash_pm[0].sequence = 2

        cls.main_pos_config.write({
            'enable_multicurrency': True,
            'currency_ids': [(4, currency_eur.id), (4, currency_usd.id)],
            'payment_method_ids': [(6, 0, [bank_pm[0].id, cash_pm[0].id])],
        })
        env['product.product'].create({
            'name': 'Payment Test Product',
            'available_in_pos': True,
            'list_price': 50.0,
            'taxes_id': False,
        })
        env.flush_all()

    def test_pos_multicurrency_payment_tour(self):
        """Execute the multi-currency payment tour on POS payment screen."""
        self.main_pos_config.with_user(self.pos_admin).open_ui()
        self.start_pos_tour('pos_multicurrency_payment_tour', login='pos_admin')
