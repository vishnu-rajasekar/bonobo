from morph_engine.model.force import Force
from morph_engine.model.force import ForceDirection
from morph_engine.model.force import ForceType


def test_force_magnitude_computed_correctly():
    force = Force(
        vector=(0, -10, 0),
        type=ForceType.LOAD,
        direction=ForceDirection.COMPRESSION,
    )
    assert force.magnitude == 10.0


def test_compression_force_direction_stored():
    force = Force(
        vector=(0, -10, 0),
        type=ForceType.LOAD,
        direction=ForceDirection.COMPRESSION,
    )
    assert force.direction == ForceDirection.COMPRESSION


def test_tension_force_direction_stored():
    force = Force(
        vector=(0, 10, 0),
        type=ForceType.MEMBER,
        direction=ForceDirection.TENSION,
    )
    assert force.direction == ForceDirection.TENSION


def test_force_vector_normalization():
    force = Force(
        vector=(0, -10, 0),
        type=ForceType.LOAD,
        direction=ForceDirection.COMPRESSION,
    )
    assert force.normalized_vector() == (0.0, -1.0, 0.0)
