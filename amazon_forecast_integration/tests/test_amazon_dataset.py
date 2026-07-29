# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestAmazonDataset(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['ir.config_parameter'].sudo()
        cls.config.set_param(
            'amazon_forecast_integration.amazon_forecast', '1')
        cls.config.set_param(
            'amazon_forecast_integration.amazon_access_key', 'access-key')
        cls.config.set_param(
            'amazon_forecast_integration.amazon_secret_access_key',
            'secret-key')
        cls.config.set_param(
            'amazon_forecast_integration.amazon_region', 'ap-south-1')
        cls.bucket = cls.env['amazon.bucket'].create({
            'bucket_name': 'forecast-bucket',
            's3_uri': 's3://forecast-bucket/forecast.csv',
        })

    def _create_dataset(self, **values):
        default_values = {
            'table_name': 'forecast_table',
            'role_name': 'forecast_role',
            'policy_name': 'forecast_policy',
            'kms_alias': 'forecast_key',
            'dataset_group': 'forecast_group',
            'dataset': 'forecast_dataset',
            'import_job_name': 'forecast_import',
            'predictor_name': 'forecast_predictor',
            'forecast_name': 'forecast',
            'item_id': 'product-a',
            'bucket_id': self.bucket.id,
            'table_arn': 'arn:aws:dynamodb:table/forecast_table',
            'role_arn': 'arn:aws:iam::123:role/forecast_role',
            'kms_arn': 'arn:aws:kms:key/1',
            'dataset_group_arn': 'arn:aws:forecast:dataset-group/1',
            'dataset_arn': 'arn:aws:forecast:dataset/1',
            'predictor_arn': 'arn:aws:forecast:predictor/1',
            'forecast_arn': 'arn:aws:forecast:forecast/1',
        }
        default_values.update(values)
        return self.env['amazon.dataset'].create(default_values)

    def _patched_session(self, clients):
        session = MagicMock()
        for client in clients.values():
            client.exceptions = SimpleNamespace(ClientError=Exception)
        session.client.side_effect = lambda service: clients[service]
        return patch(
            'odoo.addons.amazon_forecast_integration.models.amazon_dataset.'
            'boto3.Session',
            return_value=session,
        ), session

    def test_forecast_values_reads_config_parameters(self):
        values = self.env['amazon.dataset'].forecast_values()

        self.assertEqual(values['amazon_forecast'], '1')
        self.assertEqual(values['amazon_access_key'], 'access-key')
        self.assertEqual(values['amazon_secret_access_key'], 'secret-key')
        self.assertEqual(values['amazon_region'], 'ap-south-1')

    def test_action_create_table_creates_dynamodb_table(self):
        dataset = self._create_dataset()
        dynamodb_client = MagicMock()
        dynamodb_client.create_table.return_value = {
            'TableDescription': {'TableArn': 'arn:aws:dynamodb:table/new'}
        }
        patcher, session = self._patched_session({'dynamodb': dynamodb_client})

        with patcher:
            dataset.action_create_table()

        session.client.assert_called_once_with('dynamodb')
        dynamodb_client.create_table.assert_called_once()
        self.assertEqual(dataset.table_arn, 'arn:aws:dynamodb:table/new')
        self.assertEqual(dataset.state, 'role')

    def test_action_create_role_creates_forecast_role(self):
        dataset = self._create_dataset()
        iam_client = MagicMock()
        iam_client.create_role.return_value = {
            'Role': {'Arn': 'arn:aws:iam::123:role/new'}
        }
        patcher, session = self._patched_session({'iam': iam_client})

        with patcher:
            dataset.action_create_role()

        session.client.assert_called_once_with('iam')
        iam_client.create_role.assert_called_once()
        self.assertEqual(dataset.role_arn, 'arn:aws:iam::123:role/new')
        self.assertEqual(dataset.state, 'kms')

    def test_action_create_kms_creates_key_alias_and_grant(self):
        dataset = self._create_dataset()
        kms_client = MagicMock()
        kms_client.create_key.return_value = {
            'KeyMetadata': {'KeyId': 'key-id'}
        }
        kms_client.describe_key.return_value = {
            'KeyMetadata': {'Arn': 'arn:aws:kms:key/new'}
        }
        patcher, session = self._patched_session({'kms': kms_client})

        with patcher:
            key_id = dataset.action_create_kms()

        session.client.assert_called_once_with('kms')
        kms_client.create_alias.assert_called_once_with(
            AliasName='alias/forecast_key',
            TargetKeyId='key-id',
        )
        kms_client.create_grant.assert_called_once_with(
            KeyId='key-id',
            GranteePrincipal=dataset.role_arn,
            Operations=['Encrypt', 'Decrypt'],
        )
        self.assertEqual(key_id, 'key-id')
        self.assertEqual(dataset.kms_arn, 'arn:aws:kms:key/new')
        self.assertEqual(dataset.state, 'policy')

    def test_action_create_policy_creates_and_attaches_policies(self):
        dataset = self._create_dataset()
        iam_client = MagicMock()
        iam_client.create_policy.return_value = {
            'Policy': {'Arn': 'arn:aws:iam::123:policy/forecast_policy'}
        }
        sts_client = MagicMock()
        sts_client.get_caller_identity.return_value = {'Account': '123'}
        patcher, session = self._patched_session({
            'iam': iam_client,
            'sts': sts_client,
        })

        with patcher:
            dataset.action_create_policy()

        self.assertEqual(
            [call.args[0] for call in session.client.call_args_list],
            ['iam', 'sts'],
        )
        iam_client.create_policy.assert_called_once()
        iam_client.put_role_policy.assert_called_once()
        self.assertEqual(iam_client.attach_role_policy.call_count, 2)
        self.assertEqual(dataset.policy_arn,
                         'arn:aws:iam::123:policy/forecast_policy')
        self.assertEqual(dataset.state, 'dataset')

    def test_action_create_dataset_creates_dataset_group_and_dataset(self):
        dataset = self._create_dataset()
        forecast_client = MagicMock()
        forecast_client.create_dataset_group.return_value = {
            'DatasetGroupArn': 'arn:aws:forecast:dataset-group/new'
        }
        forecast_client.create_dataset.return_value = {
            'DatasetArn': 'arn:aws:forecast:dataset/new'
        }
        patcher, session = self._patched_session({'forecast': forecast_client})

        with patcher:
            dataset.action_create_dataset()

        session.client.assert_called_once_with('forecast')
        forecast_client.create_dataset_group.assert_called_once()
        forecast_client.create_dataset.assert_called_once()
        forecast_client.update_dataset_group.assert_called_once_with(
            DatasetGroupArn='arn:aws:forecast:dataset-group/new',
            DatasetArns=['arn:aws:forecast:dataset/new'],
        )
        self.assertEqual(dataset.dataset_group_arn,
                         'arn:aws:forecast:dataset-group/new')
        self.assertEqual(dataset.dataset_arn, 'arn:aws:forecast:dataset/new')
        self.assertEqual(dataset.state, 'import_dataset')

    def test_action_import_dataset_waits_until_import_is_active(self):
        dataset = self._create_dataset()
        forecast_client = MagicMock()
        forecast_client.create_dataset_import_job.return_value = {
            'DatasetImportJobArn': 'arn:aws:forecast:import-job/new'
        }
        forecast_client.describe_dataset_import_job.return_value = {
            'Status': 'ACTIVE'
        }
        patcher, session = self._patched_session({'forecast': forecast_client})

        with patcher, patch(
            'odoo.addons.amazon_forecast_integration.models.amazon_dataset.'
            'time.sleep'
        ):
            dataset.action_import_dataset()

        session.client.assert_called_once_with('forecast')
        forecast_client.create_dataset_import_job.assert_called_once()
        forecast_client.describe_dataset_import_job.assert_called_once_with(
            DatasetImportJobArn='arn:aws:forecast:import-job/new',
        )
        self.assertEqual(dataset.import_job_arn,
                         'arn:aws:forecast:import-job/new')
        self.assertEqual(dataset.state, 'predictor')

    def test_action_import_dataset_raises_when_import_fails(self):
        dataset = self._create_dataset()
        forecast_client = MagicMock()
        forecast_client.create_dataset_import_job.return_value = {
            'DatasetImportJobArn': 'arn:aws:forecast:import-job/new'
        }
        forecast_client.describe_dataset_import_job.return_value = {
            'Status': 'FAILED'
        }
        patcher, _session = self._patched_session({'forecast': forecast_client})

        with patcher, self.assertRaises(UserError):
            dataset.action_import_dataset()

    def test_action_create_predictor_creates_predictor_after_imports(self):
        dataset = self._create_dataset()
        forecast_client = MagicMock()
        forecast_client.describe_dataset_group.return_value = {
            'DatasetArns': [dataset.dataset_arn]
        }
        forecast_client.list_dataset_import_jobs.return_value = {
            'DatasetImportJobs': [{'Status': 'ACTIVE'}]
        }
        forecast_client.describe_dataset.return_value = {
            'DataFrequency': 'D'
        }
        forecast_client.create_predictor.return_value = {
            'PredictorArn': 'arn:aws:forecast:predictor/new'
        }
        patcher, session = self._patched_session({'forecast': forecast_client})

        with patcher, patch(
            'odoo.addons.amazon_forecast_integration.models.amazon_dataset.'
            'time.sleep'
        ):
            dataset.action_create_predictor()

        session.client.assert_called_once_with('forecast')
        forecast_client.create_predictor.assert_called_once()
        self.assertEqual(dataset.predictor_arn,
                         'arn:aws:forecast:predictor/new')
        self.assertEqual(dataset.state, 'forecast')

    def test_action_create_forecast_waits_until_forecast_is_active(self):
        dataset = self._create_dataset()
        forecast_client = MagicMock()
        forecast_client.create_forecast.return_value = {
            'ForecastArn': 'arn:aws:forecast:forecast/new'
        }
        forecast_client.describe_forecast.return_value = {'Status': 'ACTIVE'}
        patcher, session = self._patched_session({'forecast': forecast_client})

        with patcher, patch(
            'odoo.addons.amazon_forecast_integration.models.amazon_dataset.'
            'time.sleep'
        ):
            dataset.action_create_forecast()

        session.client.assert_called_once_with('forecast')
        forecast_client.create_forecast.assert_called_once_with(
            ForecastName='forecast',
            PredictorArn=dataset.predictor_arn,
        )
        self.assertEqual(dataset.forecast_arn,
                         'arn:aws:forecast:forecast/new')
        self.assertEqual(dataset.state, 'query_forecast')

    def test_action_create_forecast_raises_when_creation_fails(self):
        dataset = self._create_dataset()
        forecast_client = MagicMock()
        forecast_client.create_forecast.return_value = {
            'ForecastArn': 'arn:aws:forecast:forecast/new'
        }
        forecast_client.describe_forecast.return_value = {'Status': 'FAILED'}
        patcher, _session = self._patched_session({'forecast': forecast_client})

        with patcher, patch(
            'odoo.addons.amazon_forecast_integration.models.amazon_dataset.'
            'time.sleep'
        ), self.assertRaises(UserError):
            dataset.action_create_forecast()

    def test_query_forecast_returns_client_action(self):
        dataset = self._create_dataset()
        forecast_client = MagicMock()
        forecast_client.query_forecast.return_value = {
            'Forecast': {'Predictions': []}
        }
        patcher, session = self._patched_session({
            'forecastquery': forecast_client,
        })

        with patcher:
            action = dataset.query_forecast()

        session.client.assert_called_once_with('forecastquery')
        forecast_client.query_forecast.assert_called_once_with(
            ForecastArn=dataset.forecast_arn,
            Filters={'item_id': dataset.item_id},
        )
        self.assertEqual(action, {
            'type': 'ir.actions.client',
            'tag': 'forecast',
        })
