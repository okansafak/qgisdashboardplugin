try:
    from qgis.core import NULL
except ImportError:
    NULL = None

def _ok(val):
    return val is not None and val != NULL

def _nums(features, field):
    vals = []
    for f in features:
        v = f[field]
        if _ok(v):
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                pass
    return vals

def _fmt(value):
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    if value == int(value):
        return f"{int(value):,}"
    return f"{value:.2f}"
