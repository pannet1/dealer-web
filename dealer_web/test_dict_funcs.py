def add(params):
    print(params['number'] * params['value'])
    return multiply


def multiply(params):
    print(params['number'] * params['value'])
    return None  # No more operations


# List of dictionaries, each specifying operation parameters and next operation
operation_sequence = [
    {'number': 5, 'value': 2, 'func': 'add'},
    {'number': 7, 'value': 3, 'func': 'multiply'},
    # Add more dictionaries as needed
]

# Continue the loop until all 'func' values become None
while any(entry['func'] for entry in operation_sequence):
    for params in operation_sequence:
        current_function = params['func']
        if current_function:
            next_function = current_function(params)
            params['func'] = next_function
        else:
            print(f"Unknown operation: {params['func']}")
