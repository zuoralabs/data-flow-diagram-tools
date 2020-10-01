"""

TODO: handle name clashes
TODO: use kanren for graph traversal

"""

from __future__ import annotations

import abc
from fractions import Fraction
from typing import (
    List,
    Dict,
    Iterable,
    Any,
    Tuple,
    Union,
    Sequence,
    Collection,
    ClassVar,
)
import attr
from toolz import groupby, sliding_window
from werkzeug.datastructures import ImmutableList


class Element:
    name: Union[str, Tuple[str, ...]]
    comment: str = None
    aspects: Sequence[Tuple[AspectType, Element]]


@attr.s(auto_attribs=True, frozen=True)
class TrustZone(Element):
    name: str


@attr.s(auto_attribs=True)
class Account(TrustZone):
    name: str


@attr.s(auto_attribs=True)
class DataType(Element):
    name: str
    comment: str = None
    details: Sequence[Any] = attr.ib(factory=ImmutableList, converter=ImmutableList)
    aspects: Sequence[Tuple[AspectType, Element]] = attr.ib(
        factory=ImmutableList, converter=ImmutableList
    )


@attr.s(auto_attribs=True)
class Store(Element):
    type: DataType
    owner: Actor

    @property
    def name(self):
        return self.type.name, self.owner.name


@attr.s(auto_attribs=True)
class Flow(Element):
    type: DataType
    producer: Actor
    consumer: Actor

    @property
    def name(self):
        return self.type.name, self.producer.name, self.consumer.name


@attr.s(auto_attribs=True)
class MultiFlow:
    types: Sequence[DataType]
    producers: Sequence[Actor]
    consumers: Sequence[Actor]

    @property
    def derived_elements(self):
        for _type in self.types:
            for producer in self.producers:
                for consumer in self.consumers:
                    derived_element = Flow(
                        type=_type, producer=producer, consumer=consumer
                    )
                    yield derived_element


@attr.s(auto_attribs=True)
class FlowPath:
    types: List[DataType]
    path: List[Actor]

    @property
    def derived_elements(self):
        for _type in self.types:
            for producer, consumer in sliding_window(2, self.path):
                derived_element = Flow(type=_type, producer=producer, consumer=consumer)
                yield derived_element


@attr.s(auto_attribs=True, frozen=True)
class PredicateVariable(Element):
    """
    For use in QuantifiedGraph

    :attr auto_aspect: automatically infer aspect when it appears as an aspect to another element.

    """

    name: str
    element_type: type
    aspects: Sequence[Tuple[AspectType, Element]] = attr.ib(
        factory=ImmutableList, converter=ImmutableList
    )


@attr.s(auto_attribs=True, frozen=True)
class Actor(Element):
    """
    Actors can produce or pass along information. Which actor produces
    something should be derived from more basic facts.
    """

    name: str
    trust_zones: Sequence[TrustZone] = attr.ib(
        converter=ImmutableList, factory=ImmutableList
    )
    aspects: Sequence[Tuple[AspectType, Element]] = attr.ib(
        converter=ImmutableList, factory=ImmutableList
    )


@attr.s(auto_attribs=True, frozen=True)
class RequirementType:
    name: str


@attr.s(auto_attribs=True)
class Requirement:
    """
    Note: trustees are a non-exclusive list on a per requirement basis.
    Any actor not listed as a trustee in some requirement is not a trustee.
    """

    types: Collection[RequirementType]
    beneficiaries: Collection[Actor]
    trustees: Collection[Actor]
    flows: List[Flow] = attr.ib(factory=list, converter=list)
    data_types: Collection[DataType] = attr.ib(factory=list, converter=list)

    def expand(self, graph):
        """If data_types is not empty, derive the relevant flows."""
        for flow in graph.flows:
            if flow.type in self.data_types:
                self.flows.append(flow)


@attr.s(auto_attribs=True, frozen=True)
class Protection(abc.ABC):
    trustees: Collection[Actor]
    reliability: ClassVar[Fraction]  # 1 - probability of penetration in a year
    security_properties: Collection[RequirementType]

    @abc.abstractmethod
    def fill(self, graph: Graph, requirement: Requirement):
        pass


@attr.s(auto_attribs=True, frozen=True)
class ProtectionWithMembers(Protection, abc.ABC):
    members: Collection[Actor]


def fill_requirements(graph: Graph):
    unfilled_requirements = []

    for requirement in graph.requirements:

        for pp in graph.protections:
            requirement = pp.fill(graph, requirement)

        if requirement:
            unfilled_requirements.append(requirement)

    return unfilled_requirements


@attr.s
class Graph:
    # when this is true, it means that if a data flow is not
    # in the graph, then it is not permitted.
    flow_omission_equals_restriction: bool = attr.ib(default=False)

    actors: Dict[str, Actor] = attr.ib(factory=dict)
    flows: Dict[Tuple, Flow] = attr.ib(factory=dict)
    stores: Dict[Tuple, Store] = attr.ib(factory=dict)
    requirements: List[Requirement] = attr.ib(factory=list)
    protections: List[Protection] = attr.ib(factory=list)

    def inputs(self, actor: Actor) -> Iterable[Flow]:
        pass

    def outputs(self, actor: Actor) -> Iterable[Flow]:
        pass

    def update_actors(self, actors: Iterable[Actor]):
        self.actors.update(make_collection(*actors))

    def update(self, elements: Iterable[Union[Flow, FlowPath, Store, Actor]]):
        collection = make_collection(*elements)

        groups = groupby(lambda x: type(x[1]), collection.items())
        self.actors.update(groups.get(Actor, ()))
        self.stores.update(groups.get(Store, ()))
        self.flows.update(groups.get(Flow, ()))

    def update_requirements(self, requirements: Iterable[Requirement]):
        self.requirements.extend(requirements)

    def update_protections(self, protections: Iterable[Protection]):
        self.protections.extend(protections)


class Quantifier:
    predicate_variables: PredicateVariable


@attr.s(auto_attribs=True)
class ForAll(Quantifier):
    predicate_variables: PredicateVariable


@attr.s
class QuantifiedGraph(Graph):
    """A graph which is quantified over as in predicate logic

    :attribute universal_quantification_variables:
        variables over which the whole graph, as a statement, is universally quantified.

    For a concrete range of quantification, the QuantifiedGraph
    is a cartesian product of loops over the quantification variables. However,
    the range may be abstract, and we may not want to look at the fully expanded
    graph in any case.

    NB: "comprehension" is from list comprehensions in CS.

    Example
    --------

    Trust relationships and flows are separated by locking variables.

    For example, actors and data types can have the locking variable "tenant".
    If an actor and a data type with the "tenant" locking variable show up
    in a flow, this implies the concrete data flows are separated by
    tenant. This same separation applies to requirements.
    """

    quantifiers: List[Quantifier] = attr.ib(factory=list)


@attr.s(auto_attribs=True, frozen=True)
class AspectType:
    name: str


def add_to_collection(collection: Dict, *elements: Element):
    for element in elements:
        if isinstance(element, (MultiFlow, FlowPath)):
            for derived_element in element.derived_elements:
                collection[derived_element.name] = derived_element
        else:
            collection[element.name] = element


def make_collection(*elements):
    collection = {}
    add_to_collection(collection, *elements)
    return collection
