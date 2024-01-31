import os.path


class ScreencopyListener():

    ROBOT_LISTENER_API_VERSION = 2

    def __init__(self, file_name='listen.txt'):
        path = os.path.join(os.path.curdir, file_name)
        self.file = open(path, 'w')

    def start_suite(self, name, attrs):
        self.file.write(f"start_suite: {name}, {attrs['doc']}\n")

    def start_test(self, name, attrs):
        tags = ' '.join(attrs['tags'])
        self.file.write(f"start_test: {name} - {attrs['doc']} [ {tags} ] :: ")


    def start_keyword(self, name, attrs):
        self.file.write(f"start_keyword: {name}\n")

    def end_keyword(self, name, attrs):
        self.file.write(f"end_keyword: {name}\n")

    def end_test(self, name, attrs):
        if attrs['status'] == 'PASS':
            self.file.write('PASS\n')
        else:
            self.file.write(f"FAIL: {attrs['message']}\n")

    def end_suite(self, name, attrs):
        self.file.write(f"end_suite: {name}, {attrs['status']}, {attrs['message']}\n")

    def close(self):
        self.file.close()
