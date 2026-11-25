"""python -m hx.scenes: who draws what. Every registered span by time, and the gaps the placeholder fills."""
from ..timeline import get_timeline
from . import spans

end, t = get_timeline().duration, 0.0
for t0, t1, name in spans():
    if t0 > t + 1e-6:
        print(f"{t:8.2f} - {t0:8.2f}   (free: placeholder)")
    print(f"{t0:8.2f} - {t1:8.2f}   {name}{'   (stand-in: a real scene wins over it)' if name.startswith('demo_') else ''}")
    t = max(t, t1)
if t < end - 1e-6:
    print(f"{t:8.2f} - {end:8.2f}   (free: placeholder)")
