from django.conf.urls import url, include
from rest_framework import routers

from Core.monitor import Monitor
from Core.views import *
from Data.views import *

router = routers.DefaultRouter()
router.register(r'api/v1/core/baseauth', BaseAuthView, base_name="BaseAuth")
router.register(r'api/v1/core/currentuser', CurrentUserView, base_name="CurrentUser")
router.register(r'api/v1/core/setting', SettingView)
router.register(r'api/v1/core/project', ProjectView, base_name="Project")
router.register(r'api/v1/core/task', TaskView, base_name="Task")
router.register(r'api/v1/core/humantaskapi', HumanTaskAPIView, base_name="HumanTaskAPI")
router.register(r'api/v1/data/ipaddress', IPaddressView, base_name="IPaddress")
router.register(r'api/v1/data/port', PortView, base_name="Port")
router.register(r'api/v1/data/website', WebsiteView, base_name="Website")
urlpatterns = [
    url(r'^', include(router.urls)),
]

Monitor()

# celery -A Worker.Common.tasks worker -l info -E -P gevent
