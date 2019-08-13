from rest_framework.generics import *
from rest_framework.response import *
from rest_framework.viewsets import *

from Data.data import *


# Create your views here.
class IPaddressView(ModelViewSet, UpdateAPIView, DestroyAPIView):
    queryset = IPaddressModel.objects.all()
    serializer_class = IPaddressSerializer

    def list(self, request, **kwargs):
        """查询数据库中的host信息"""
        try:
            pid = int(request.headers.get('pid', 0))
            context = IPaddress.list(pid)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)

    def destroy(self, request, pk=None, **kwargs):
        try:
            id = int(request.query_params.get('id', -1))
            context = IPaddress.destory(id)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)


class PortView(ModelViewSet, UpdateAPIView, DestroyAPIView):
    queryset = PortModel.objects.all()
    serializer_class = PortSerializer

    def list(self, request, **kwargs):
        """查询数据库中的host信息"""
        try:
            ipid = int(request.query_params.get('ipid', -1))
            context = Port.list(ipid)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)

    def destroy(self, request, pk=None, **kwargs):
        try:
            id = int(request.query_params.get('id', -1))
            context = Port.destory(id)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)


# Create your views here.
class WebsiteView(ModelViewSet, UpdateAPIView, DestroyAPIView):
    queryset = WebsiteModel.objects.all()
    serializer_class = WebsiteSerializer

    def list(self, request, **kwargs):
        """查询数据库中的host信息"""
        try:
            pid = int(request.headers.get('pid', 0))
            context = Website.list(pid)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = list_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)

    def create(self, request, pk=None, **kwargs):
        """更新host信息到数据库"""
        try:
            pid = int(request.headers.get('pid', 0))
            domain = str(request.data.get('domain', None))
            websites = request.data.get('websites', None)
            context = Website.create(pid=pid, domain=domain, websites=websites)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)

    def destroy(self, request, pk=None, **kwargs):
        try:
            id = int(request.query_params.get('id', -1))
            context = Website.destory(id)
        except Exception as E:
            logger.error(E)
            CODE = 500
            context = dict_data_return(CODE, CODE_MESSAGE.get(CODE), {})
        return Response(context)
