import yaml
import boto3
from django.core.management import BaseCommand
from django.conf import settings
import subprocess
import sys


class Command(BaseCommand):
    help = "creates a session table if does not exist"

    def add_arguments(self, parser):
        parser.add_argument(
            '--template_file', '--template_file',
            help='String',
            dest='template_file'
        )
        parser.add_argument(
            '--table_name', '--table_name',
            default='journeyTable',
            help='String',
            dest='table_name'
        )
        parser.add_argument(
            '--read_capacity_units', '--read_capacity_units',
            default=5,
            type=int,
            help='Integer',
            dest='read_capacity_units'
        )
        parser.add_argument(
            '--write_capacity_units', '--write_capacity_units',
            default=5,
            type=int,
            help='Integer',
            dest='write_capacity_units'
        )

    def handle(self, *args, **options):
        template_file = options.get('template_file')
        table_name = options.get('table_name')
        read_capacity_units = options.get('read_capacity_units')
        write_capacity_units = options.get('write_capacity_units')

        with open(template_file, 'r') as f:
            template = yaml.safe_load(f)

        dynamodb_client = boto3.client(
            'dynamodb',
            endpoint_url='http://dynamodb:8000',
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )

        for resource_name, resource_config in template['Resources'].items():
            if resource_config.get('Type') == 'AWS::DynamoDB::Table':
                table_properties = resource_config.get('Properties', {})

                # Replace the table name with the one from the command line
                table_properties['TableName'] = table_name

                # Resolve CloudFormation Ref for ReadCapacityUnits and WriteCapacityUnits
                if 'ProvisionedThroughput' in table_properties:
                    if isinstance(table_properties['ProvisionedThroughput'].get('ReadCapacityUnits'), dict) and \
                            'Ref' in table_properties['ProvisionedThroughput']['ReadCapacityUnits']:
                        table_properties['ProvisionedThroughput']['ReadCapacityUnits'] = read_capacity_units
                    if isinstance(table_properties['ProvisionedThroughput'].get('WriteCapacityUnits'), dict) and \
                            'Ref' in table_properties['ProvisionedThroughput']['WriteCapacityUnits']:
                        table_properties['ProvisionedThroughput']['WriteCapacityUnits'] = write_capacity_units

                # The boto3 create_table function doesn't accept all the properties from the CloudFormation template
                # so we need to filter them out.
                valid_properties = [
                    'TableName', 'AttributeDefinitions', 'KeySchema', 'ProvisionedThroughput',
                    'LocalSecondaryIndexes', 'GlobalSecondaryIndexes', 'StreamSpecification',
                    'SSESpecification', 'Tags'
                ]
                create_table_args = {k: v for k, v in table_properties.items() if k in valid_properties}

                try:
                    dynamodb_client.create_table(**create_table_args)
                    self.stdout.write(self.style.SUCCESS(f"Successfully created table: {table_name}"))
                except dynamodb_client.exceptions.ResourceInUseException:
                    self.stdout.write(self.style.WARNING(f"Table {table_name} already exists."))
                    pass
