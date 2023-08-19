from datetime import date

def display_amount(amount: int) -> str:
    return f'{amount // 100},{amount % 100:02d}'

def value_or_null(obj, name: str, commas: bool = True) -> str:
    optionalComma = ', ' if commas else ''
    value = getattr(obj, name)
    if value is None:
        strValue = 'null'
    elif isinstance(value, (str, date)):
        strValue = f'"{value}"'
    else:
        strValue = str(value)
    return f'{optionalComma}{strValue}'



