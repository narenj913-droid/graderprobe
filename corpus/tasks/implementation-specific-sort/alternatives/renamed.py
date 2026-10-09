def sort_values(values):
    data = list(values)
    count = len(data)
    for i in range(count):
        for j in range(0, count - i - 1):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data
