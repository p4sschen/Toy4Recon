import ipaddress as ipaddressmodule

from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.generics import *
from rest_framework.permissions import *
from rest_framework.response import *
from rest_framework.viewsets import *

from Core.celeryTask import PORTSCAN
from Core.core import *


class BaseAuthView(ModelViewSet, UpdateAPIView, DestroyAPIView):
    queryset = None  # 设置类的queryset
    serializer_class = AuthTokenSerializer  # 设置类的serializer_class
    permission_classes = (AllowAny,)

    def create(self, request, pk=None, **kwargs):
        """更新host信息到数据库"""
        nullResponse = {"status": "error", "type": "account", "currentAuthority": "guest",
                        "token": "forguest"}
        try:
            serializer = AuthTokenSerializer(data=request.data)
            if serializer.is_valid():
                token, created = Token.objects.get_or_create(user=serializer.validated_data['user'])

                time_now = datetime.datetime.now()

                if created or token.created < time_now - datetime.timedelta(minutes=EXPIRE_MINUTES):
                    # Update the created time of the token to keep it valid
                    token.delete()
                    token = Token.objects.create(user=serializer.validated_data['user'])
                    token.created = time_now
                    token.save()
                nullResponse['status'] = 'ok'
                nullResponse['currentAuthority'] = 'admin'  # 当前为单用户模式,默认为admin
                nullResponse['token'] = token.key
                return Response(nullResponse)

            return Response(nullResponse)
        except Exception as E:
            logger.error(E)
            return Response(nullResponse)


class CurrentUserView(ModelViewSet, UpdateAPIView, DestroyAPIView):
    queryset = None  # 设置类的queryset
    serializer_class = ProjectSerializer  # 设置类的serializer_class

    def list(self, request, **kwargs):
        """查询数据库中的host信息"""
        user = request.user

        context = CurrentUser.list(user)  # token是Token数据类型
        return Response(context)


class SettingView(ModelViewSet, UpdateAPIView, DestroyAPIView):
    queryset = SettingModel.objects.all()  # 设置类的queryset
    serializer_class = SettingSerializer  # 设置类的serializer_class

    def list(self, request, **kwargs):
        """查询数据库中的host信息"""
        try:
            kind = str(request.query_params.get('kind', None))
            activated = request.query_params.get('activated', None)

            context = Settings.list(kind=kind, activated=activated)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)

    def create(self, request, pk=None, **kwargs):
        """更新host信息到数据库"""

        try:
            kind = str(request.data.get('kind', None))
            tag = str(request.data.get('tag', None))
            setting = request.data.get('setting', None)
            context = Settings.create(kind=kind, tag=tag, setting=setting)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)

    def update(self, request, pk=None, **kwargs):
        """更新host信息到数据库"""

        try:
            id = int(request.data.get('id', None))
            activating = request.data.get('activating', False)
            tag = str(request.data.get('tag', None))
            setting = request.data.get('setting', None)
            context = Settings.update(id=id, activating=activating, tag=tag, setting=setting)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)

    def destroy(self, request, pk=None, **kwargs):

        try:
            id = int(request.query_params.get('id', -1))
            context = Settings.destory(id=id)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)


# GET（SELECT）：从服务器取出资源（一项或多项）
# 当GET, PUT和PATCH请求成功时，要返回对应的数据，及状态码200，即SUCCESS
# 当GET 不到数据时，状态码要返回404，即NOT FOUND
# 任何时候，如果请求有问题，如校验请求数据时发现错误，要返回状态码 400，即BAD REQUEST
# 当API 请求需要用户认证时，如果request中的认证信息不正确，要返回状态码 401，即NOT AUTHORIZED
# 当API 请求需要验证用户权限时，如果当前用户无相应权限，要返回状态码 403，即FORBIDDEN
# POST（CREATE）：在服务器新建一个资源
# 当POST创建数据成功时，要返回创建的数据，及状态码201，即CREATED
# 当POST创建数据失败时，要返回空数据，及状态码405(自定义的状态码)，即CREATED FAIL

class ProjectView(ModelViewSet, UpdateAPIView, DestroyAPIView):
    queryset = ProjectModel.objects.all()  # 设置类的queryset
    serializer_class = ProjectSerializer  # 设置类的serializer_class

    def list(self, request, **kwargs):
        """查询数据库中的host信息"""
        context = Project.list()
        return Response(context)

    def create(self, request, pk=None, **kwargs):
        """更新host信息到数据库"""
        try:
            tag = str(request.data.get('tag', None))
            name = str(request.data.get('name', None))
            desc = str(request.data.get('desc', None))
            context = Project.create(tag, name, desc)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)

    def update(self, request, pk=None, **kwargs):
        """更新host信息到数据库"""
        try:
            id = int(request.data.get('id', None))
            tag = str(request.data.get('tag', None))
            name = str(request.data.get('name', None))
            desc = str(request.data.get('desc', None))
            context = Project.update(id, tag, name, desc)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)

    def destroy(self, request, pk=None, **kwargs):
        try:
            id = int(request.query_params.get('id', -1))
            context = Project.destory(id)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)


class HumanTaskAPIView(ModelViewSet, UpdateAPIView, DestroyAPIView):
    queryset = TaskModel.objects.all()  # 设置类的queryset
    serializer_class = TaskSerializer  # 设置类的serializer_class

    def create(self, request, pk=None, **kwargs):
        """更新host信息到数据库"""
        try:
            pid = int(request.headers.get('pid', 0))
            kind = str(request.data.get('kind', None))

            if kind == PORTSCAN:
                ipaddress = str(request.data.get('ipaddress', None))
                domain = str(request.data.get('domain', None))
                ipaddresses = ipaddressmodule.IPv4Network("{}/24".format(ipaddress), False)
                startip = ipaddresses[0].compressed
                stopip = ipaddresses[-1].compressed
                kwargs = {"startip": startip, "stopip": stopip, 'domain': domain}
                context = Task.create(pid, kind, kwargs)
            else:
                CODE = 500
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)


class TaskView(ModelViewSet, UpdateAPIView, DestroyAPIView):
    queryset = TaskModel.objects.all()  # 设置类的queryset
    serializer_class = TaskSerializer  # 设置类的serializer_class

    def list(self, request, **kwargs):
        """查询数据库中的host信息"""
        try:
            pid = int(request.headers.get('pid', 0))
            context = Task.list(pid)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)

    def create(self, request, pk=None, **kwargs):
        """更新host信息到数据库"""
        try:
            pid = int(request.headers.get('pid', 0))
            kind = str(request.data.get('kind', None))
            kwargs = request.data.get('kwargs', None)
            if isinstance(kwargs, str) or isinstance(kwargs, bytes):
                kwargs = json.loads(kwargs)
                context = Task.create(pid, kind, kwargs)
            elif isinstance(kwargs, dict):
                context = Task.create(pid, kind, kwargs)
            else:
                CODE = 500
                context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)

    def destroy(self, request, pk=None, **kwargs):
        try:
            id = int(request.query_params.get('id', -1))
            context = Task.destory(id)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)
