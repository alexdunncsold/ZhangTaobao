import configparser


class FbGroup:
    def __init__(self, nickname):
        config = configparser.ConfigParser()
        config.read_file(open('group_config.ini', 'r', encoding="utf-8"))  # must handle Chinese characters
        self.id = config[nickname]['Id']
        self.name = config[nickname]['Name']
        self.tz = config[nickname]['Timezone']
