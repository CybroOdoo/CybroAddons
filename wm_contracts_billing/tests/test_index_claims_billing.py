from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'wm_billing')
class TestIndexClaimsBilling(TransactionCase):
    """Numbers advertised on the Apps-store page, plus the consolidated-invoice
    event discount."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.partner = cls.env['res.partner'].create({'name': 'Index Claims Customer'})
        cls.point = cls.env['wm.collection.point'].create({'name': 'Index Claims Site', 'partner_id': cls.partner.id})
        cls.category = cls.env['wm.waste.category'].create({'name': 'Index Claims Waste', 'code': 'IDXCLM', 'price': 2.0})
        cls.sla = cls.env['wm.sla'].create({'name': 'Index Claims SLA', 'terms_and_conditions': 'Terms'})

    def _contract(self, **vals):
        values = {
            'name': 'Index Claims Contract', 'partner_id': self.partner.id, 'sla_id': self.sla.id,
            'from_date': self.today - timedelta(days=90), 'to_date': self.today + timedelta(days=90),
            'frequency': 'monthly', 'no_of_frequency': 1, 'state': 'ongoing',
            'collection_point_ids': [(6, 0, self.point.ids)],
        }
        values.update(vals)
        return self.env['wm.partner.contract'].create(values)

    def test_consolidated_invoice_applies_event_discount(self):
        """An extra-pickup subscriber discount reaches the consolidated invoice line too."""
        event = self.env['wm.billable.event'].create({
            'partner_id': self.partner.id, 'event_type': 'extra_pickup', 'event_date': self.today,
            'quantity': 1.0, 'price_unit': 100.0, 'discount_pct': 20.0, 'state': 'confirmed'})
        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner.id,
            'date_from': self.today - timedelta(days=1),
            'date_to': self.today + timedelta(days=1),
        })
        consolidated.action_generate_invoice()
        line = consolidated.invoice_id.invoice_line_ids.filtered(lambda ln: ln.display_type == 'product')
        self.assertAlmostEqual(line.discount, 20.0)
        self.assertAlmostEqual(consolidated.invoice_id.amount_untaxed, 80.0)
        self.assertEqual(event.state, 'invoiced')

    def test_overweight_and_hybrid_amounts(self):
        """Overweight is charged per 10 kg above the allowance."""
        Order = self.env['wm.collection.order']
        pc = self._contract(billing_basis='per_collection', fixed_price=100.0, max_weight=500.0,
                            overweight_price=10.0)
        rule = Order._get_billing_rule(self.category, self.partner, self.today, contract=pc)
        base, surcharge, over_kg, _allowed = Order._compute_collection_fee(rule, 700.0, 1)
        self.assertEqual((base, over_kg), (100.0, 200.0))
        self.assertAlmostEqual(surcharge, 200.0)  # 20 blocks of 10 kg x 10
        pc.state = 'cancelled'
        hy = self._contract(billing_basis='hybrid', fixed_price=100.0, included_weight=100.0,
                            overweight_price=10.0)
        rule = Order._get_billing_rule(self.category, self.partner, self.today, contract=hy)
        base, surcharge, *_r = Order._compute_collection_fee(rule, 250.0, 1)
        self.assertAlmostEqual(base + surcharge, 250.0)

    def test_minimum_charge_applies_per_collection(self):
        rule = self.env['wm.pricing.rule'].create({
            'waste_category_id': self.category.id, 'price_per_kg': 2.0, 'min_charge': 50.0})
        Order = self.env['wm.collection.order']
        found = Order._get_billing_rule(self.category, self.partner, self.today)
        self.assertEqual(found.id, rule.id)
        total, _billed, applied = Order._price_per_kg_per_collection(found, [5.0, 100.0])
        self.assertTrue(applied)
        self.assertAlmostEqual(total, 50.0 + 200.0)
