from __future__ import annotations

from fractions import Fraction
from itertools import groupby
from typing import Dict, Tuple, Sequence, Union, Final, Collection

import attr

from data_flow_elements.core import (
    Actor,
    TrustZone,
    Flow,
    make_collection,
    DataType,
    Requirement,
    MultiFlow,
    FlowPath,
    PredicateVariable,
    Graph,
    QuantifiedGraph,
    ForAll,
    AspectType,
    Store,
    Protection,
    ProtectionWithMembers,
)
from data_flow_elements.naming import (
    EnumMixin,
    AutoNumberEnum,
    make_namespace,
    Name,
    auto_names,
)
from data_flow_elements.security import (
    AuthenticationSecret,
    Authentication,
    secrecy,
    integrity,
    availability,
    Uses,
    IsTenantSpecific,
)
from enum import Enum, auto
import data_flow_elements.vis
import dominate as dom
import dominate.tags
from pathlib import Path


@make_namespace
class NS:
    """
    Namespace for managing strings
    """

    customer = Name()
    customer_authentication = Name()

    service_1 = Name()

    service_2 = Name()

    tenant = Name()

    red_data = Name()
    blue_data = Name()

    creds = Name()


@auto_names
class TrustZones:
    first_tz = TrustZone(Name())
    second_tz = TrustZone(Name())


@auto_names
class AspectTypes:
    tenant = AspectType(Name())


@auto_names
class Vars:
    tenant = PredicateVariable(NS.tenant, TrustZone)


graph = QuantifiedGraph(quantifiers=[ForAll(Vars.tenant)])


red_data = DataType(NS.red_data, aspects=[(AspectTypes.tenant, Vars.tenant)])
blue_data = DataType(NS.blue_data, aspects=[(AspectTypes.tenant, Vars.tenant)])

creds = AuthenticationSecret(NS.creds, details=[IsTenantSpecific()])

graph.update(
    [
        Actor(NS.customer, trust_zones=[], aspects=[(AspectTypes.tenant, Vars.tenant)]),
        Actor(NS.service_1, trust_zones=[TrustZones.first_tz]),
        Actor(NS.service_2, trust_zones=[TrustZones.second_tz]),
    ]
)


graph.update(
    [
        FlowPath(
            types=[red_data],
            path=[
                graph.actors[NS.customer],
                graph.actors[NS.service_1],
                graph.actors[NS.service_2],
            ],
        ),
        Flow(
            type=Authentication(
                NS.customer_authentication,
                details=[Uses(creds), IsTenantSpecific(True)],
            ),
            producer=graph.actors[NS.customer],
            consumer=graph.actors[NS.service_1],
        ),
    ]
)

graph.update_requirements(
    [
        # customer is ultimate beneficiary
        Requirement(
            types=[secrecy, integrity, availability],
            data_types=[red_data],
            trustees=[
                graph.actors[NS.customer],
                graph.actors[NS.service_1],
                graph.actors[NS.service_2],
            ],
            beneficiaries=[graph.actors[NS.customer], graph.actors[NS.customer]],
        ),
    ]
)


graph.update_protections(
    [
        # TODO: make some examples
    ]
)


@attr.s(auto_attribs=True)
class ProseCollection:
    heading: str
    items: Sequence[Union[str, ProseCollection]]

    def to_html_tags(self, heading_level=2):
        heading_tag = [
            None,
            dom.tags.h1,
            dom.tags.h2,
            dom.tags.h3,
            dom.tags.h4,
            dom.tags.h5,
            dom.tags.h6,
        ][heading_level]

        def _item_to_html_tags(item):
            if isinstance(item, ProseCollection):
                return item.to_html_tags(heading_level=heading_level + 1)
            else:
                return item

        return dom.tags.div(
            heading_tag(self.heading),
            dom.tags.ul([dom.tags.li(_item_to_html_tags(item)) for item in self.items]),
        )


dot = data_flow_elements.vis.create_diagram_2(name="example", graph=graph,)

dot.render("generated/diagram", view=True, format="png")


def create_html_page(doc: dom.document, graph: Graph):
    doc.add(
        dom.tags.h1("Data Flow Diagram"), dom.tags.img(src=Path("diagram.png")),
    )

    doc.add(dom.tags.h2("Fixed requirements"))
    doc.add(
        dom.tags.ul(
            dom.tags.li(
                f"Req.{ii}",
                dom.tags.ul(
                    [
                        dom.tags.li("Types: " + ", ".join([x.name for x in req.types])),
                        dom.tags.li(
                            "Beneficiaries: "
                            + ", ".join([x.name for x in req.beneficiaries])
                        ),
                        dom.tags.li(
                            "Trustees: " + ", ".join([x.name for x in req.trustees])
                        ),
                        dom.tags.li(
                            "Flows: "
                            + ", ".join(
                                [
                                    x.producer.name
                                    + f" --[{x.type.name}]-> "
                                    + x.consumer.name
                                    for x in req.flows
                                ]
                            )
                        )
                        if req.flows
                        else "",
                        dom.tags.li(
                            "Data types: " + ", ".join([x.name for x in req.data_types])
                        )
                        if req.data_types
                        else "",
                    ]
                ),
            )
            for ii, req in enumerate(graph.requirements)
        )
    )

    doc.add(dom.tags.h2("Derived requirements"))
    doc.add(dom.tags.div("TODO"))


with dom.document(title="data flow model") as doc:
    create_html_page(doc, graph)

    Path("generated/data_flow_model.html").write_text(doc.render())
