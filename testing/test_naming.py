from data_flow_elements.naming import make_namespace, Name


@make_namespace
class NS:
    x = Name()
    y = Name("special")
    z = ""


def test_make_ns():
    assert NS.x == "x"
    assert NS.y == "special"
    assert NS.z == ""
