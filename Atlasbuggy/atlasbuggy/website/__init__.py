from flask import Flask, render_template
from atlasbuggy.datastream import DataStream
from atlasbuggy.files import BaseFile


class Website(DataStream):
    def __init__(self, template_folder, static_folder, flask_params=None, app_params=None, enabled=True, debug=False,
                 name=None, use_index=True, host='0.0.0.0', port=5000):
        if flask_params is None:
            flask_params = {}

        template_folder = BaseFile.get_full_dir(template_folder)
        static_folder = BaseFile.get_full_dir(static_folder)

        self.host = host
        self.port = port

        self.app = Flask(__name__, template_folder=template_folder, static_folder=static_folder, **flask_params)

        if use_index:
            self.app.add_url_rule("/", "index", self.index)

        if app_params is not None:
            self.app_params = app_params
        else:
            self.app_params = {}

        super(Website, self).__init__(enabled, debug, True, False, name)

    def index(self):
        """
        app.add_url_rule('/', 'hello', hello_world)

        Is the same as:

        @app.route('/hello')
        def hello_world():
           return 'hello world'
        """
        return render_template('index.html')

    def run(self):
        self.app.run(host=self.host, port=self.port, debug=False, threaded=True, **self.app_params)
