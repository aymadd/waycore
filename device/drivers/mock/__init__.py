from .altimeter import register as _reg_altimeter  # noqa: F401
from .camera import register as _reg_camera  # noqa: F401
from .gps import register as _reg_gps  # noqa: F401
from .mesh_network import register as _reg_mesh_network  # noqa: F401
from .module_port import register as _reg_module_port  # noqa: F401
from .power import register as _reg_power  # noqa: F401
from .radio import register as _reg_radio  # noqa: F401
from .sensor import register as _reg_sensor  # noqa: F401

# Trigger registrations on import of package
_reg_altimeter(None)
_reg_camera(None)
_reg_gps(None)
_reg_mesh_network(None)
_reg_radio(None)
_reg_sensor(None)
_reg_module_port(None)
_reg_power(None)

__all__: list[str] = []
