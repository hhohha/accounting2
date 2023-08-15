from datetime import date

def nameIfPresent(obj, name: str) -> str:
    return name + ', ' if getattr(obj, name) is not None else ''

def valueIfPresent(obj, name: str) -> str:
    return f', {str(getattr(obj, name))} ' if getattr(obj, name) is not None else ''

def valueOrNull(obj, name: str, commas: bool = True) -> str:
    optionalComma = ', ' if commas else ''
    value = getattr(obj, name)
    if value is None:
        strValue = 'null'
    elif isinstance(value, (str, date)):
        strValue = f'"{value}"'
    else:
        strValue = str(value)
    return f'{optionalComma}{strValue}'