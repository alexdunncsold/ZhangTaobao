class FacebookGroup:
    name = ''
    id = ''

    def __init__(self, name, id):
        if len(id) != 15:
            raise ValueError('FacebookGroup __init__(): supplied id {} invalid'.format(id))

        self.name = name
        self.id = id
