test:
	@docker-compose run app python manage.py test

base_image:
	docker build -t  mwaaas/django_ussd_airflow:base_image -f BaseDockerfile .

compile_documentation:
	docker-compose run app make -C /usr/src/app/docs html

create_dynamodb_table:
	docker-compose run ansible ./create_dynamodb.sh
