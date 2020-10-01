from collections import defaultdict
from typing import Dict
from uuid import uuid4

from graphviz import Digraph

from diagrams import Diagram, Edge, Cluster
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB
from diagrams.onprem.compute import Server
from diagrams.onprem.client import Client
from diagrams.oci import security

from diagrams.programming.language import Python

from .core import Graph, Actor, Flow, AspectType, Element, ProtectionWithMembers


def create_diagram(*, graph: Graph, name="Web Service", show=True):
    with Diagram(name, show=show):
        nodes = {}
        for name, aa in graph.actors.items():
            if "customer" in name:
                nodes[name] = Client(label=name)
            else:
                nodes[name] = Server(label=name)

        aa: Actor
        for name, aa in graph.actors.items():
            clusters = [Cluster(cluster.name) for cluster in aa.trust_zones]
            node = nodes[name]
            for cluster in clusters:
                cluster.node(node._id, node.label, **node._attrs)

        # ELB("lb") >> EC2("web") >> RDS("userdb") >> ss

        ff: Flow
        for name, ff in graph.flows.items():
            nodes[ff.producer.name] >> Edge(label=ff.type.name) >> nodes[
                ff.consumer.name
            ]


def create_label(aa: Element):
    label = aa.name
    aspect_type: AspectType
    maybe_inner_args = ", ".join(
        f"{aspect_type.name}={aspect.name}" for aspect_type, aspect in aa.aspects
    )
    if maybe_inner_args:
        label += f"({maybe_inner_args})"
    return label


def create_diagram_2(
    *, graph: Graph, name="Web Service", show=True, graph_engine=None
) -> Digraph:
    dot = Digraph(comment="name", engine=graph_engine)
    dot.attr(
        rankdir="LR",
        ranksep="0.2",
        # pad='3',
    )

    protection_back_refs = defaultdict(set)

    for protection in graph.protections:
        if isinstance(protection, ProtectionWithMembers):
            for member in protection.members:
                protection_back_refs[member].add(protection)

    aa: Actor
    nodes: Dict[Actor, str] = {}
    for name, aa in graph.actors.items():
        nodes[aa] = str(uuid4())
        label = (
            create_label(aa)
            + "\n"
            + "".join(
                getattr(protection, "icon") for protection in protection_back_refs[aa]
            )
        )

        dot.node(name=nodes[aa], label=label, shape="box", style="rounded")

    edges = defaultdict(list)
    ff: Flow
    for name, ff in graph.flows.items():
        edges[(nodes[ff.producer], nodes[ff.consumer])].append(create_label(ff.type))

    for (source, dest), labels in edges.items():
        dot.edge(
            tail_name=source, label=",\n".join(labels), head_name=dest, minlen="3",
        )

    return dot
