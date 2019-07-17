class FacebookGroup:
    name = ''
    id = ''

    def __init__(self, name, id):
        if not 15 <= len(id) <= 16:
            raise ValueError('FacebookGroup __init__(): supplied id {} invalid'.format(id))

        self.name = name
        self.id = id
