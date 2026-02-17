from django.urls import re_path, include
from django.contrib import admin
from ussd.views import AfricasTalkingUssdGateway

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^africastalking_gateway',
        AfricasTalkingUssdGateway.as_view(),
        name='africastalking_url'),
    re_path(r'^ussd_airflow/', include('ussd.urls'))
]

