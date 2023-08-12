def nameIfPresent(obj, name: str) -> str:
    return name + ', ' if getattr(obj, name) is not None else ''

def valueIfPresent(obj, name: str) -> str:
    return f', {str(getattr(obj, name))} ' if getattr(obj, name) is not None else ''

def valueOrNull(obj, name: str) -> str:
    return f', {str(getattr(obj, name))} ' if getattr(obj, name) is not None else ', null '