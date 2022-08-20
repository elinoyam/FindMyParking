def most_common_highest_probablity():
    file = open("probabilities.osm", "r")
    bucket_list = [0] * 168
    for line in file.readlines():
        if line.startswith('\t\t<tag'):
            index = line.index('v')
            end = len(line) - line[::-1].index('"') -1
            temp_list = line[index+3:end].split(',')
            for index in range(len(temp_list)):
                if temp_list[index] not in ['', '0']:
                    bucket_list[index] += 1
    return bucket_list.index(max(bucket_list))


