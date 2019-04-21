
def truncate_middle(string: str, size: int) -> str:
    if size < 3:
        raise ValueError("cannot truncate to less than 3 characters")
    if size >= len(string):
        return string

    end_size = (size - 3) // 2
    return string[:end_size] + '...' + string[len(string)-end_size:]