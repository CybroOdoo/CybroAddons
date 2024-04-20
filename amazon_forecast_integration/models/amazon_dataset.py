# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
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
import boto3
import json
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AmazonDataset(models.Model):
    """Class to create a forecast of stock"""
    _name = "amazon.dataset"
    _description = "Amazon Dataset"
    _rec_name = "table_name"

    table_name = fields.Char(string="Table Name", required=True,
                             help="Provide the table name.")
    role_name = fields.Char(string="Role Name",
                            help="Provide the Role name.")
    policy_name = fields.Char(string="Policy Name",
                              help="Provide the Policy name.")
    dataset_group = fields.Char(string="Dataset Group",
                                help="Provide the Dataset Group name.")
    dataset = fields.Char(string="Dataset",
                          help="Provide the Dataset name.")
    state = fields.Selection([
        ('table', "Table"),
        ('role', "Role"),
        ('kms', "KMS"),
        ('policy', "Policy"),
        ('dataset', "Dataset"),
        ('import_dataset', "Import Dataset"),
        ('predictor', "Predictor"),
        ('forecast', "Forecast"),
        ('query_forecast', "Query Forecast"),
    ], default="table", string="State",
        help="States of dataset creation.")
    table_arn = fields.Char(string="Table ARN",
                            help="Table arn will be computed based on table"
                                 " name provided after creating the table.")
    role_arn = fields.Char(string="Role Arn", help="Role Arn will be computed "
                                                   "after Role is created.")
    policy_arn = fields.Char(string="Policy Arn",
                             help="Policy Arn will be created after the "
                                  "policy is created.")
    kms_alias = fields.Char(string="KMS Alias Name",
                            help="Provide an Alias name for KMS.")
    kms_arn = fields.Char(string="KMS Arn", help="KMS Arn will be created "
                                                 "after KMS key is created.")
    dataset_group_arn = fields.Char(string="Dataset Group Arn",
                                    help="Dataset Group Arn will be created "
                                         "after Dataset Group is created.")
    dataset_arn = fields.Char(string="Dataset Arn",
                              help="Dataset Arn will be craeted after"
                                   " Dataset is created.")
    forecast_frequency = fields.Selection([
        ('D', 'Days'),
        ('W', 'Weeks'),
        ('M', 'Months'),
        ('Y', 'Years'),
        ('T', 'Minutes'),
        ('H', 'Hours'),
    ], default='D', string="Forecast Frequency", help="Choose the frequency"
                                                      " for forecasting.")
    import_job_name = fields.Char(string="Import Job Name",
                                  help="Provide the import job name.")
    import_job_arn = fields.Char(string="Import Job Arn",
                                 help="Import job Arn will be computed after"
                                      " import job is done.")
    predictor_name = fields.Char(string="Predictor Name",
                                 help="Provide a name for Predictor function.")
    predictor_algorithm = fields.Selection([
        ('arn:aws:forecast:::algorithm/ARIMA', 'ARIMA'),
        ('arn:aws:forecast:::algorithm/CNN-QR', 'CNN-QR'),
        ('arn:aws:forecast:::algorithm/NPTS', 'NPTS'),
        ('arn:aws:forecast:::algorithm/MQRNN', 'MQRNN'),
    ], string="Algorithm", default='arn:aws:forecast:::algorithm/ARIMA',
        help="Choose desired Predictor Algorithm.")
    predictor_arn = fields.Char(string="Predictor Arn",
                                help="Predictor Arn will be computed after "
                                     "predictor function is created.")
    forecast_name = fields.Char(string="Forecast Name",
                                help="Provide the name for forecast function.")
    forecast_arn = fields.Char(string="Forecast Arn",
                               help="Forecast Arn will be computed after "
                                    "forecasting is completed.")
    item_id = fields.Char(string="Item id",
                          help="Provide the name of product you want to know "
                               "the forecasting.")
    bucket_id = fields.Many2one('amazon.bucket', string="Bucket",
                                help="Choose the bucket name "
                                                    "from which the data must"
                                                    "be taken.")

    def forecast_values(self):
        """To connect with the Amazon Forecast services using credentials"""
        amazon_forecast = self.env['ir.config_parameter'].sudo().get_param(
            'amazon_forecast_integration.amazon_forecast')
        amazon_access_key = self.env['ir.config_parameter'].sudo().get_param(
            'amazon_forecast_integration.amazon_access_key')
        amazon_secret_access_key = self.env[
            'ir.config_parameter'].sudo().get_param(
            'amazon_forecast_integration.amazon_secret_access_key')
        amazon_region = self.env['ir.config_parameter'].sudo().get_param(
            'amazon_forecast_integration.amazon_region')
        return {
            'amazon_forecast': amazon_forecast,
            'amazon_access_key': amazon_access_key,
            'amazon_secret_access_key': amazon_secret_access_key,
            'amazon_region': amazon_region,
        }

    def action_create_table(self):
        """To create a dynamodb in Amazon Forecast"""
        values = self.forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            dynamodb_client = session.client('dynamodb')
            try:
                response = dynamodb_client.create_table(
                    TableName=self.table_name,
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'id',
                            'AttributeType': 'N'
                        }
                    ],
                    KeySchema=[
                        {
                            'AttributeName': 'id',
                            'KeyType': 'HASH'
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                self.write({
                    'state': 'role',
                    'table_arn': response['TableDescription']['TableArn']
                })
            except dynamodb_client.exceptions.ClientError as e:
                raise UserError(e)

    def action_create_role(self):
        """To create a Role for Forecasting"""
        values = self.forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            assume_role_policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "forecast.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            iam_client = session.client('iam')
            try:
                response = iam_client.create_role(
                    RoleName=self.role_name,
                    AssumeRolePolicyDocument=json.dumps(
                        assume_role_policy_document)
                )
                self.write({
                    'state': 'kms',
                    'role_arn': response['Role']['Arn']
                })
            except iam_client.exceptions.ClientError as e:
                raise UserError(e)

    def action_create_kms(self):
        """To create a Key Management Service in AWS"""
        values = self.forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            kms_client = session.client('kms')
            response = kms_client.create_key(
                Description='KMS Key'
            )
            key_id = response['KeyMetadata']['KeyId']
            key_response = kms_client.describe_key(KeyId=key_id)
            key_arn = key_response['KeyMetadata']['Arn']
            self.write({
                'kms_arn': key_arn,
            })
            kms_client.create_alias(
                AliasName='alias/'+self.kms_alias,
                TargetKeyId=key_id
            )
            kms_client.create_grant(
                KeyId=key_id,
                GranteePrincipal=self.role_arn,
                Operations=['Encrypt', 'Decrypt']
            )
            self.write({
                'state': 'policy'
            })
            return key_id

    def action_create_policy(self):
        """To create a policies for the role and attach it with the role"""
        values = self.forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            iam_client = session.client('iam')
            sts_client = session.client('sts')
            response = sts_client.get_caller_identity()
            account_id = response['Account']
            policy_name = self.policy_name
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:ListBucket"
                        ],
                        "Resource": "arn:aws:s3:::"+self.bucket_id.bucket_name
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObject",
                            "s3:PutObject"
                        ],
                        "Resource":
                            "arn:aws:s3:::"+self.bucket_id.bucket_name+"/*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:PutItem",
                            "dynamodb:GetItem"
                        ],
                        "Resource": self.table_arn
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "kms:Encrypt",
                            "kms:Decrypt",
                            "kms:ReEncrypt*",
                            "kms:GenerateDataKey*",
                            "kms:DescribeKey",
                            "kms:CreateGrant"
                        ],
                        "Resource": self.kms_arn
                    }
                ]
            }
            response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
            )
            self.write({
                'policy_arn': response['Policy']['Arn']
            })
            try:
                iam_client.put_role_policy(
                    RoleName=self.role_name,
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_document)
                )
            except Exception as e:
                raise UserError(e)
            try:
                policy_arn1 = 'arn:aws:iam::aws:policy/AmazonS3FullAccess'
                policy_arn2 = (
                        'arn:aws:iam::'+account_id+':policy/'+self.policy_name)
                iam_client.attach_role_policy(
                    RoleName=self.role_name,
                    PolicyArn=policy_arn1
                )
                iam_client.attach_role_policy(
                    RoleName=self.role_name,
                    PolicyArn=policy_arn2
                )
                self.write({
                    'state': 'dataset'
                })
            except iam_client.exceptions.ClientError as e:
                raise UserError(e)
            except iam_client.exceptions.ClientError as e:
                raise UserError(e)

    def action_create_dataset(self):
        """To create required Dataset for forecasting"""
        values = self.forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            dataset_group_name = self.dataset_group
            forecast_client = session.client('forecast')
            try:
                dataset_group_response = forecast_client.create_dataset_group(
                    DatasetGroupName=dataset_group_name,
                    Domain='RETAIL',
                    Tags=[
                        {'Key': 'Name', 'Value': dataset_group_name}
                    ]
                )
                self.write({'dataset_group_arn': dataset_group_response[
                    'DatasetGroupArn']})
                dataset_name = self.dataset
            except forecast_client.exceptions.ClientError as e:
                raise UserError(e)
            try:
                schema = {
                    "Attributes": [
                        {"AttributeName": "item_id",
                         "AttributeType": "string"},
                        {"AttributeName": "timestamp",
                         "AttributeType": "timestamp"},
                        {"AttributeName": "demand",
                         "AttributeType": "float"},
                        {"AttributeName": "id", "AttributeType": "string"},
                        {"AttributeName": "reference",
                         "AttributeType": "string"},
                        {"AttributeName": "location_id",
                         "AttributeType": "string"},
                        {"AttributeName": "location_dest_id",
                         "AttributeType": "string"},
                        {"AttributeName": "origin",
                         "AttributeType": "string"},
                    ]
                }
                dataset_response = forecast_client.create_dataset(
                    DatasetName=dataset_name,
                    DatasetType='TARGET_TIME_SERIES',
                    Domain='RETAIL',
                    DataFrequency=self.forecast_frequency,
                    Schema=schema,
                    EncryptionConfig={
                        'RoleArn': self.role_arn,
                        'KMSKeyArn': self.kms_arn,
                    }
                )
                self.write({
                    'dataset_arn': dataset_response['DatasetArn']
                })
                forecast_client.update_dataset_group(
                    DatasetGroupArn=self.dataset_group_arn,
                    DatasetArns=[self.dataset_arn])
                self.write({
                    'state': 'import_dataset'
                })
            except forecast_client.exceptions.ClientError as e:
                raise UserError(e)

    def action_import_dataset(self):
        """To import dataset from Amazon S3 bucket"""
        values = self.forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            forecast_client = session.client('forecast')
            try:
                response = forecast_client.create_dataset_import_job(
                    DatasetImportJobName=self.import_job_name,
                    DatasetArn=self.dataset_arn,
                    DataSource={
                        'S3Config': {
                            'Path': self.bucket_id.s3_uri,
                            'RoleArn': self.role_arn
                        }
                    }
                )
                self.write({
                    'import_job_arn': response['DatasetImportJobArn'],
                    'state': 'predictor'
                })
                while True:
                    response = forecast_client.describe_dataset_import_job(
                        DatasetImportJobArn=self.import_job_arn)
                    status = response['Status']
                    if status == 'ACTIVE':
                        break
                    elif status == 'FAILED' or status == 'CREATE_FAILED':
                        raise UserError(_('Error: Dataset Import Job failed.'))
                        break
                    else:
                        time.sleep(10)
            except forecast_client.exceptions.ClientError as e:
                raise UserError(e)

    def action_create_predictor(self):
        """To create the predictor function for forecasting"""
        values = self.forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            forecast_client = session.client('forecast')
            try:
                response_group = forecast_client.describe_dataset_group(
                    DatasetGroupArn=self.dataset_group_arn)
                dataset_arns = response_group['DatasetArns']
                while True:
                    all_datasets_imported = True
                    for dataset_arn in dataset_arns:
                        response = forecast_client.list_dataset_import_jobs(
                            Filters=[{'Key': 'DatasetArn',
                                      'Value': dataset_arn,
                                      'Condition': 'IS'}])
                        import_jobs = response["DatasetImportJobs"]
                        if (len(import_jobs) == 0 or
                                import_jobs[0]["Status"] != "ACTIVE"):
                            all_datasets_imported = False
                            break
                    if all_datasets_imported:
                        break
                    time.sleep(10)
                response = forecast_client.describe_dataset(
                    DatasetArn=self.dataset_arn)
                featurization_config = response['DataFrequency']
                response = forecast_client.create_predictor(
                    PredictorName=self.predictor_name,
                    AlgorithmArn=self.predictor_algorithm,
                    ForecastHorizon=1,
                    PerformAutoML=False,
                    PerformHPO=False,
                    InputDataConfig={
                        'DatasetGroupArn': self.dataset_group_arn,
                    },
                    FeaturizationConfig={
                        'ForecastFrequency': featurization_config,
                    }
                )
                self.write({
                    'predictor_arn': response['PredictorArn'],
                    'state': 'forecast'
                })
            except forecast_client.exceptions.ClientError as e:
                raise UserError(e)

    def action_create_forecast(self):
        """To create the forecast based on our data"""
        values = self.forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            forecast_client = session.client('forecast')
            try:
                response = forecast_client.create_forecast(
                    ForecastName=self.forecast_name,
                    PredictorArn=self.predictor_arn
                )
                self.write({
                    'forecast_arn': response['ForecastArn'],
                    'state': 'query_forecast'
                })
                while True:
                    response = forecast_client.describe_forecast(
                        ForecastArn=response['ForecastArn'])
                    status = response['Status']
                    if status == 'ACTIVE':
                        break
                    elif status == 'FAILED':
                        raise UserError(_('Error: Forecast creation failed.'))
                        break
                    else:
                        time.sleep(10)
            except forecast_client.exceptions.ClientError as e:
                raise UserError(e)
        time.sleep(60)

    def query_forecast(self):
        """To get the forecast result"""
        values = self.forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            forecast_client = session.client('forecastquery')
            try:
                forecast_client.query_forecast(
                    ForecastArn=self.forecast_arn,
                    Filters={
                        'item_id': self.item_id
                    }
                )
                return {
                    'type': 'ir.actions.client',
                    'tag': 'forecast',
                }
            except forecast_client.exceptions.ClientError as e:
                raise UserError(e)

    @api.model
    def get_query_result(self):
        """To get the response from the query forecast"""
        values = self.forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            forecast_client = session.client('forecastquery')
            data = self.search([], limit=1)
            response = forecast_client.query_forecast(
                ForecastArn=data.forecast_arn,
                Filters={
                    'item_id': data.item_id
                }
            )
            forecast_result = response['Forecast']['Predictions']
            return forecast_result
