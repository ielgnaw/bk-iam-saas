# -*- coding: utf-8 -*-
"""
TencentBlueKing is pleased to support the open source community by making 蓝鲸智云-权限中心(BlueKing-IAM) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""
from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.api.authentication import ESBAuthentication
from backend.api.mixins import ExceptionHandlerMixin
from backend.audit.audit import audit_context_setter, view_audit_decorator
from backend.common.swagger import ResponseSwaggerAutoSchema
from backend.service.models import Subject
from backend.trans.open_authorization import AuthorizationTrans

from ..audit import SubjectPolicyGrantOrRevokeAuditProvider
from ..constants import AuthorizationAPIEnum, VerifyAPIParamLocationEnum
from ..mixins import AuthViewMixin
from ..permissions import AuthorizationAPIPermission
from ..serializers import AuthBatchInstanceSLZ, AuthBatchPathSLZ, AuthInstanceSLZ, AuthPathSLZ


class AuthInstanceView(AuthViewMixin, ExceptionHandlerMixin, APIView):
    """
    单个资源授权回收
    """

    authentication_classes = [ESBAuthentication]
    permission_classes = [AuthorizationAPIPermission]
    authorization_api_permission = {
        "post": (VerifyAPIParamLocationEnum.ACTION_IN_BODY.value, AuthorizationAPIEnum.AUTHORIZATION_INSTANCE.value),
    }

    trans = AuthorizationTrans()

    @swagger_auto_schema(
        operation_description="单个资源授权回收",
        auto_schema=ResponseSwaggerAutoSchema,
        request_body=AuthInstanceSLZ,
        responses={status.HTTP_200_OK: serializers.Serializer()},
        tags=["open"],
    )
    @view_audit_decorator(SubjectPolicyGrantOrRevokeAuditProvider)
    def post(self, request, *args, **kwargs):
        serializer = AuthInstanceSLZ(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        operate = data["operate"]
        subject = Subject(**data["subject"])
        system_id = data["system"]
        expired_at = data["expired_at"]
        action_id = data["action"]["id"]
        resources = data["resources"]

        # 转换为策略列表
        policy_list = self.trans.to_policy_list_for_instance(system_id, action_id, resources, expired_at)

        # 授权或回收
        policies = self.grant_or_revoke(operate, subject, policy_list)

        audit_context_setter(operate=operate, subject=subject, system_id=system_id, policies=policies)

        return Response({"policy_id": policies[0].policy_id})


class AuthPathView(AuthViewMixin, ExceptionHandlerMixin, APIView):
    """
    单个拓扑层级授权/回收
    """

    authentication_classes = [ESBAuthentication]
    permission_classes = [AuthorizationAPIPermission]
    authorization_api_permission = {
        "post": (VerifyAPIParamLocationEnum.SYSTEM_IN_BODY.value, AuthorizationAPIEnum.AUTHORIZATION_INSTANCE.value),
    }

    trans = AuthorizationTrans()

    @swagger_auto_schema(
        operation_description="单个拓扑层级授权/回收",
        auto_schema=ResponseSwaggerAutoSchema,
        request_body=AuthPathSLZ,
        responses={status.HTTP_200_OK: serializers.Serializer()},
        tags=["open"],
    )
    @view_audit_decorator(SubjectPolicyGrantOrRevokeAuditProvider)
    def post(self, request, *args, **kwargs):
        serializer = AuthPathSLZ(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        operate = data["operate"]
        subject = Subject(**data["subject"])
        system_id = data["system"]
        expired_at = data["expired_at"]
        action_id = data["action"]["id"]
        resources = data["resources"]

        # 转换为策略列表
        policy_list = self.trans.to_policy_list_for_path(system_id, action_id, resources, expired_at)

        # 授权或回收
        policies = self.grant_or_revoke(operate, subject, policy_list)

        audit_context_setter(operate=operate, subject=subject, system_id=system_id, policies=policies)

        return Response({"policy_id": policies[0].policy_id})


class AuthBatchInstanceView(AuthViewMixin, ExceptionHandlerMixin, APIView):
    """
    批量操作批量资源授权回收
    """

    authentication_classes = [ESBAuthentication]
    permission_classes = [AuthorizationAPIPermission]
    authorization_api_permission = {
        "post": (VerifyAPIParamLocationEnum.ACTIONS_IN_BODY.value, AuthorizationAPIEnum.AUTHORIZATION_INSTANCE.value),
    }

    trans = AuthorizationTrans()

    @swagger_auto_schema(
        operation_description="批量操作批量资源授权回收",
        auto_schema=ResponseSwaggerAutoSchema,
        request_body=AuthBatchInstanceSLZ,
        responses={status.HTTP_200_OK: serializers.Serializer()},
        tags=["open"],
    )
    @view_audit_decorator(SubjectPolicyGrantOrRevokeAuditProvider)
    def post(self, request, *args, **kwargs):
        serializer = AuthBatchInstanceSLZ(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        operate = data["operate"]
        subject = Subject(**data["subject"])
        system_id = data["system"]
        expired_at = data["expired_at"]
        action_ids = [a["id"] for a in data["actions"]]
        resources = data["resources"]

        # 转换为策略列表
        policy_list = self.trans.to_policy_list_for_instances(system_id, action_ids, resources, expired_at)

        # 授权或回收
        policies = self.grant_or_revoke(operate, subject, policy_list)

        audit_context_setter(operate=operate, subject=subject, system_id=system_id, policies=policies)

        return Response([{"action": {"id": p.action_id}, "policy_id": p.policy_id} for p in policies])


class AuthBatchPathView(AuthViewMixin, ExceptionHandlerMixin, APIView):
    """
    批量操作批量拓扑层级授权/回收
    """

    authentication_classes = [ESBAuthentication]
    permission_classes = [AuthorizationAPIPermission]
    authorization_api_permission = {
        "post": (VerifyAPIParamLocationEnum.SYSTEM_IN_BODY.value, AuthorizationAPIEnum.AUTHORIZATION_INSTANCE.value),
    }

    trans = AuthorizationTrans()

    @swagger_auto_schema(
        operation_description="批量操作批量拓扑层级授权/回收",
        auto_schema=ResponseSwaggerAutoSchema,
        request_body=AuthBatchPathSLZ,
        responses={status.HTTP_200_OK: serializers.Serializer()},
        tags=["open"],
    )
    @view_audit_decorator(SubjectPolicyGrantOrRevokeAuditProvider)
    def post(self, request, *args, **kwargs):
        serializer = AuthBatchPathSLZ(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        operate = data["operate"]
        subject = Subject(**data["subject"])
        system_id = data["system"]
        expired_at = data["expired_at"]
        action_ids = [a["id"] for a in data["actions"]]
        resources = data["resources"]

        # 转换为策略列表
        policy_list = self.trans.to_policy_list_for_paths(system_id, action_ids, resources, expired_at)

        # 授权或回收
        policies = self.grant_or_revoke(operate, subject, policy_list)

        audit_context_setter(operate=operate, subject=subject, system_id=system_id, policies=policies)

        return Response([{"action": {"id": p.action_id}, "policy_id": p.policy_id} for p in policies])
