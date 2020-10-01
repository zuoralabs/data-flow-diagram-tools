import setuptools

setuptools.setup(
    name="data_flow_diagram_tools",
    packages=["data_flow_elements"],
    install_requires=["boto3", "toolz", "attrs", "graphviz", "Werkzeug", "dominate"],
    tests_require=["pytest"],
    version="0.1.0",
    classifiers=["Programming Language :: Python :: 3.8"],
)
