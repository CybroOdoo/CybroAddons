from types import SimpleNamespace
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase

from odoo.addons.manpower_supply_management.controllers import manpower_supply_management


class FakeModel:
    def __init__(self, records=None):
        self.records = records or []
        self.created_vals = None
        self.search_domain = None
        self.browse_id = None

    def sudo(self):
        return self

    def search(self, domain):
        self.search_domain = domain
        return self.records

    def create(self, vals):
        self.created_vals = vals
        return SimpleNamespace(id=99)

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


class TestWebsiteFormController(TransactionCase):
    def _call_route(self, controller, method_name, *args, **kwargs):
        method = getattr(controller, method_name)
        return method.original_endpoint(controller, *args, **kwargs)

    def _patch_request(self, user=None, models=None):
        user = user or SimpleNamespace(id=7, _is_admin=lambda: False)
        fake_request = FakeRequest(FakeEnv(user, models or {}), user)
        return fake_request, patch.object(
            manpower_supply_management,
            "request",
            fake_request,
        )

    def test_labour_supply_renders_form_for_current_user(self):
        user = SimpleNamespace(id=7, _is_admin=lambda: False)
        fake_request, request_patch = self._patch_request(user=user)

        with request_patch:
            controller = manpower_supply_management.WebsiteForm()
            result = self._call_route(controller, "labour_supply")

        self.assertEqual(
            result["template"],
            "manpower_supply_management.online_labour_supply_form",
        )
        self.assertEqual(result["values"]["customer"], user)
        self.assertEqual(fake_request.render_calls[0], result)

    def test_labour_supply_renders_all_users_for_admin(self):
        users_model = FakeModel(records=["admin", "demo"])
        user = SimpleNamespace(id=1, _is_admin=lambda: True)
        fake_request, request_patch = self._patch_request(
            user=user,
            models={"res.users": users_model},
        )

        with request_patch:
            controller = manpower_supply_management.WebsiteForm()
            result = self._call_route(controller, "labour_supply")

        self.assertEqual(result["values"]["customer"], ["admin", "demo"])
        self.assertEqual(users_model.search_domain, [])
        self.assertEqual(fake_request.render_calls[0], result)

    def test_create_labour_supply_rejects_invalid_dates(self):
        user = SimpleNamespace(id=7, _is_admin=lambda: False)
        fake_request, request_patch = self._patch_request(user=user)

        with request_patch:
            controller = manpower_supply_management.WebsiteForm()
            result = self._call_route(
                controller,
                "create_labour_supply",
                customer_id="7",
                from_date="2000-01-02",
                to_date="2000-01-01",
            )

        self.assertEqual(
            result["template"],
            "manpower_supply_management.online_labour_supply_form",
        )
        self.assertTrue(result["values"]["alert"])
        self.assertEqual(fake_request.render_calls[0], result)

    def test_create_labour_supply_creates_contract_and_renders_skill_form(self):
        skill_model = FakeModel(records=["Skill A"])
        contract_model = FakeModel()
        fake_request, request_patch = self._patch_request(
            models={
                "skill.details": skill_model,
                "labour.supply": contract_model,
            },
        )

        with request_patch:
            controller = manpower_supply_management.WebsiteForm()
            result = self._call_route(
                controller,
                "create_labour_supply",
                customer_id="7",
                from_date=str(fields.Date.today()),
                to_date=str(fields.Date.today()),
            )

        self.assertEqual(
            result["template"],
            "manpower_supply_management.labour_on_supply_form",
        )
        self.assertEqual(contract_model.created_vals["customer_id"], "7")
        self.assertEqual(result["values"]["skills"], ["Skill A"])
        self.assertEqual(fake_request.render_calls[0], result)

    def test_create_labour_on_supply_rejects_invalid_dates(self):
        skill_model = FakeModel(records=["Skill A"])
        contract_model = FakeModel()
        fake_request, request_patch = self._patch_request(
            models={
                "skill.details": skill_model,
                "labour.supply": contract_model,
            },
        )

        with request_patch:
            controller = manpower_supply_management.WebsiteForm()
            result = self._call_route(
                controller,
                "create_labour_on_supply",
                labour_supply="42",
                skill="3",
                from_date="2000-01-02",
                to_date="2000-01-01",
                required_number="2",
            )

        self.assertEqual(
            result["template"],
            "manpower_supply_management.labour_on_supply_form",
        )
        self.assertTrue(result["values"]["alert"])
        self.assertEqual(contract_model.browse_id, 42)

    def test_create_labour_on_supply_adds_skill_line(self):
        skill_model = FakeModel(records=["Skill A"])
        contract_model = FakeModel()
        line_model = FakeModel()
        fake_request, request_patch = self._patch_request(
            models={
                "skill.details": skill_model,
                "labour.supply": contract_model,
                "labour.on.skill": line_model,
            },
        )

        with request_patch:
            controller = manpower_supply_management.WebsiteForm()
            result = self._call_route(
                controller,
                "create_labour_on_supply",
                labour_supply="42",
                skill="3",
                from_date=str(fields.Date.today()),
                to_date=str(fields.Date.today()),
                required_number="2",
            )

        self.assertEqual(
            result["template"],
            "manpower_supply_management.labour_on_supply_form",
        )
        self.assertEqual(line_model.created_vals["labour_supply_id"], "42")
        self.assertEqual(contract_model.browse_id, 42)

    def test_create_labour_on_supply_completed_renders_success(self):
        fake_request, request_patch = self._patch_request()

        with request_patch:
            controller = manpower_supply_management.WebsiteForm()
            result = self._call_route(
                controller,
                "create_labour_on_supply_completed",
            )

        self.assertEqual(
            result["template"],
            "manpower_supply_management.tmp_form_success",
        )
        self.assertEqual(fake_request.render_calls[0], result)

