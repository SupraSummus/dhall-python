if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) != 2:
        print('usage: {} variable_name'.format(sys.argv[0]), file=sys.stderr)
        exit(1)
    variable_name = sys.argv[1]

    value = json.load(sys.stdin)
    print('{} = {}'.format(variable_name, repr(value)))
