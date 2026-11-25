"""hx.chalk: the kit of film version 4, "the child's own drawing" (chalk and crayon on dark paper).

Read hx/chalk/README.md, then the part docs in hx/chalk/doc/. Everything a scene needs:

    from hx.chalk import *
"""
from .core import *            # noqa: F401,F403
from .core import TAB, a8, lowfreq, white   # noqa: F401
from .sketch import Fill, Sketch, Stroke, closed, line, morph   # noqa: F401
from .ground import GROUND_X, GROUND_Y, ground_line   # noqa: F401
from .figure import *          # noqa: F401,F403
from .people import *          # noqa: F401,F403
from .gloom import *           # noqa: F401,F403
from .weather import *         # noqa: F401,F403
from .sets import *            # noqa: F401,F403
from .things import *          # noqa: F401,F403
from .land import *            # noqa: F401,F403
from .hills import *           # noqa: F401,F403
from .day import *             # noqa: F401,F403
from . import title            # noqa: F401
from . import acting_child, acting_pair   # noqa: F401  (both define Act: use them as modules, never star-import them)
