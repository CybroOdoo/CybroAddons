from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests.common import TransactionCase

from odoo.addons.manpower_supply_management.controllers import labour_supply


class FakeModel:
    def __init__(self, records=None):
        self.records = records or []
        self.search_domain = None
        self.browse_id = None

    def search(self, domain):
        self.search_domain = domain
        return self.records

    def browse(self, record_id):
        self.browse_id = record_id
        return SimpleNamespace(id=record_id)


class FakeEnv(dict):
    def __init__(self, user, models):
        super().__init__(models)
        self.user = user


class FakeRequest:
    def __init__(self, env, user):
        self.env = env
        self.env.user = user
        self.render_calls = []

    def render(self, template, values=None):
        result = {"template": template, "values": values or {}}
        self.render_calls.append(result)
        return result


class TestLabourSupplyPortalController(TransactionCase):
    def _call_route(self, controller, method_name, *args, **kwargs):
        method = getattr(controller, method_name)
        return method.original_endpoint(controller, *args, **kwargs)

    def test_create_labour_on_supply_lists_current_customer_contracts(self):
        user = SimpleNamespace(commercial_partner_id=SimpleNamespace(id=44))
        contract_model = FakeModel(records=["contract"])
        fake_request = FakeRequest(FakeEnv(user, {"labour.supply": contract_model}), user)

        with patch.object(labour_supply, "request", fake_request):
            controller = labour_supply.LabourSupply()
            result = self._call_route(controller, "create_labour_on_supply")

        self.assertEqual(
            result["template"],
            "manpower_supply_management.portal_labour_supply",
        )
        self.assertEqual(contract_model.search_domain, [("customer_id.id", "=", 44)])
        self.assertEqual(result["values"]["labour_supplies_portal"], ["contract"])
        self.assertEqual(result["values"]["page_name"], "labour_supplies_contract")

    def test_labour_on_supply_details_renders_contract_and_lines(self):
        user = SimpleNamespace(commercial_partner_id=SimpleNamespace(id=44))
        contract_model = FakeModel()
        line_model = FakeModel(records=["line"])
        fake_request = FakeRequest(
            FakeEnv(user, {
                "labour.supply": contract_model,
                "labour.on.skill": line_model,
            }),
            user,
        )
        fake_http = SimpleNamespace(request=fake_request)

        with patch.object(labour_supply, "request", fake_request), \
                patch.object(labour_supply, "http", fake_http):
            controller = labour_supply.LabourSupply()
            result = self._call_route(
                controller,
                "labour_on_supply_details",
                55,
            )

        self.assertEqual(
            result["template"],
            "manpower_supply_management.portal_labour_supply_details",
        )
        self.assertEqual(contract_model.browse_id, 55)
        self.assertEqual(line_model.search_domain, [("labour_supply_id", "=", 55)])
        self.assertEqual(result["values"]["labour_contract_line_rec"], ["line"])

