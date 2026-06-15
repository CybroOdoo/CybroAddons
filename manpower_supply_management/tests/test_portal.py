from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

from odoo.addons.manpower_supply_management.controllers import portal


class FakeModel:
    def __init__(self, records=None):
        self.records = records or []
        self.search_domain = None

    def search_count(self, domain):
        self.search_domain = domain
        return len(self.records)


class FakeEnv(dict):
    def __init__(self, user, models):
        super().__init__(models)
        self.user = user


class FakeRequest:
    def __init__(self, env, user):
        self.env = env
        self.env.user = user


class TestCustomerPortal(TransactionCase):
    def test_prepare_home_portal_values_adds_contract_count_when_requested(self):
        user = SimpleNamespace(commercial_partner_id=SimpleNamespace(id=44))
        contract_model = FakeModel(records=["contract"])
        fake_request = FakeRequest(FakeEnv(user, {"labour.supply": contract_model}), user)

        with patch.object(portal, "request", fake_request), \
                patch.object(
                    portal.portal.CustomerPortal,
                    "_prepare_home_portal_values",
                    MagicMock(return_value={}),
                ):
            values = portal.CustomerPortal()._prepare_home_portal_values([
                "contact_count",
            ])

        self.assertEqual(values["contact_count"], 1)
        self.assertEqual(contract_model.search_domain, [("customer_id.id", "=", 44)])

    def test_prepare_home_portal_values_skips_count_when_not_requested(self):
        user = SimpleNamespace(commercial_partner_id=SimpleNamespace(id=44))
        contract_model = FakeModel(records=["contract"])
        fake_request = FakeRequest(FakeEnv(user, {"labour.supply": contract_model}), user)

        with patch.object(portal, "request", fake_request), \
                patch.object(
                    portal.portal.CustomerPortal,
                    "_prepare_home_portal_values",
                    MagicMock(return_value={"existing": 1}),
                ):
            values = portal.CustomerPortal()._prepare_home_portal_values([])

        self.assertEqual(values, {"existing": 1})
        self.assertIsNone(contract_model.search_domain)

