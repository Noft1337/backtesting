def sketch(a: int, b: int):
    if a == b:
        return True
    elif a > b:
        return False
    else:
        raise ValueError("A IS LOWER THAN B !!!")
