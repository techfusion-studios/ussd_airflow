from django.core.management import BaseCommand
import boto3
from django.conf import settings


class Command(BaseCommand):
    help = "deletes a dynamodb table"

    def add_arguments(self, parser):
        parser.add_argument(
            '--table_name', '--table_name',
            default=settings.DYNAMODB_TABLE,
            help='String',
            dest='table_name'
        )

    def handle(self, *args, **options):
        dynamodb_client = boto3.client(
            'dynamodb',
            endpoint_url='http://dynamodb:8000',
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        try:
            dynamodb_client.delete_table(TableName=options['table_name'])
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted table: {options['table_name']}"))
        except dynamodb_client.exceptions.ResourceNotFoundException:
            self.stdout.write(self.style.WARNING(f"Table {options['table_name']} does not exist."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error deleting table {options['table_name']}: {e}"))
