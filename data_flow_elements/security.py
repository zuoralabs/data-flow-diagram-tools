"""
Data flow elements specific to security
"""
import enum
from enum import Enum
from typing import Union, List

import attr

from .naming import auto_names, Name
from .core import DataType, RequirementType, Element, Actor, Flow, Store, Requirement


@attr.s(auto_attribs=True)
class IsTenantSpecific:
    value: bool = True
    element: Element = None


@attr.s(auto_attribs=True)
class Uses:
    used: DataType
    user: DataType = None


@attr.s(auto_attribs=True)
class AuthenticationSecret(DataType):
    pass


@attr.s(auto_attribs=True)
class Authentication(DataType):
    pass


class PermissionType(enum.Enum):
    read = 4
    write = 2


@attr.s(auto_attribs=True)
class Permission(Element):
    name: str
    permission_type: PermissionType


@auto_names
class BucketPermission:
    read_objects = Permission(Name(), PermissionType.read)


@attr.s(auto_attribs=True)
class AWSAccessControlStatement:
    actors: Actor
    access_type: PermissionType
    resources: List[Union[Flow, Store, Actor]]


@attr.s(auto_attribs=True)
class AWSAccessPolicy(Element):
    statements: List[AWSAccessControlStatement]


@attr.s(auto_attribs=True)
class CompleteContext(Element):
    """
    Completeness means that all interactions not explicitly allowed are denied
    """

    subjects: List[Union[DataType, Flow, Store, Actor]]
    statements: List[Union[Requirement, AWSAccessPolicy]]


integrity = RequirementType("integrity")
secrecy = RequirementType("secrecy")
availability = RequirementType("availability")
