import sys
from django.test.runner import DiscoverRunner
from django.core import management
from os import environ
from django.conf import settings
from unittest.suite import TestSuite


if sys.argv[1] == "test":
    # patch DiscoverRunner setup database to be able to create
    # dynamo db on startup
    original_setup_database = DiscoverRunner.setup_databases

    def custom_setup_database(*args, **kwargs):
        # set the correct dynamo db name
        actual_db_name = "test_" + "django-ussd-airflow"
        db_name = settings.DATABASES["default"]['NAME']
        actual_dynamo_db_name = environ["DYNAMODB_TABLE"]

        db_suffix = db_name.replace(actual_db_name, "")

        if db_suffix:
            dynamo_db_name = "test_" + actual_dynamo_db_name + db_suffix
        else:
            dynamo_db_name = "test_" + actual_dynamo_db_name

        settings.DYNAMODB_TABLE = dynamo_db_name

        management.call_command('create_dynamo_table_from_template',
                                template_file='devops/templates/cloud-formation/dynamodb.templates.yml',
                                table_name=settings.DYNAMODB_TABLE)
        return original_setup_database(*args, **kwargs)

    DiscoverRunner.setup_databases = custom_setup_database

    # path DiscoverRunner teardown to be able to tear down dynamodb
    original_teardown_databases = DiscoverRunner.teardown_databases

    def custom_teardown_database(*args, **kwargs):
        # here we delete dynamodb table
        management.call_command('delete_dynamo_table',
                                table_name=settings.DYNAMODB_TABLE)
        return original_teardown_databases(*args, **kwargs)

    DiscoverRunner.teardown_databases = custom_teardown_database

    # now we need to be able to truncate data from dynamo db
    # each time a test is being  executed.
    original_setup_class = TestSuite._handleClassSetUp


    def custom_handle_class_setup(self, test, result):
        from ussd.store.journey_store.DynamoDb import dynamodb_table
        # here we delete all records in dynamodb

        table = dynamodb_table(
            settings.DYNAMODB_TABLE,
            "http://dynamodb:8000"
        )
        scan = table.scan()
        for item in scan['Items']:
            table.delete_item(Key={'journeyName': item.get('journeyName'), 'version': item.get('version')})

        return original_setup_class(self, test, result)


    TestSuite._handleClassSetUp = custom_handle_class_setup