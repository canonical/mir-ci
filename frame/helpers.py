def combine(*arg):
    result = [()]
    for input_list in arg:
        partial_result = result
        result = []
        for partial_tuple in partial_result:
            for input_item in input_list:
                result.append(partial_tuple + (input_item,))
    return result

def all_servers() -> list[str]:
    return [
        'ubuntu-frame',
        'mir-kiosk',
        'egmde',
    ]
