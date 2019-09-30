import configparser


class FbGroup:
    def __init__(self, nickname=None, **kwargs):
        nickname = nickname if nickname else self.get_name_for(kwargs['id'])
        config = configparser.ConfigParser()
        config.read_file(open('group_config.ini', 'r', encoding="utf-8"))  # must handle Chinese characters
        self.id = config[nickname]['Id']
        self.name = config[nickname]['Name']
        self.tz = config[nickname]['Timezone']

    # Crappy workaround until I figure out how to set up group config permanently
    @staticmethod
    def get_name_for(id):
        config = configparser.ConfigParser()
        config.read_file(open('group_config.ini', 'r', encoding="utf-8"))  # must handle Chinese characters
        for section_name in config.sections():
            if config[section_name]['Id'] == id:
                return section_name
        raise ValueError(f'Could not get nickname for group with id {id}')
