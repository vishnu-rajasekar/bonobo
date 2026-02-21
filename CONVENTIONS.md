# CONVENTIONS.md

Naming:
- Research versions use suffixes _v1, _v2
- Scripts must NOT start with test_

Testing:
- tests/ = unit tests only
- integration_tests/ = Rhino/MCP only
- scripts/ = experiments and demos

Serialization:
- StructuralGraph JSON must remain backward compatible per version
