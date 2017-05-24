from flask import Flask, render_template
from atlasbuggy.datastream import DataStream

class Website(DataStream):
    def __init__(self, flask_params, website_params=None, enabled=True, debug=False, name=None):
        self.app = Flask(__name__, **flask_params)
        self.app.add_url_rule("/", "index", self.index)
        if website_params is None:
            self.website_params = website_params
        else:
            self.website_params = {}

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
        self.app.run(host='0.0.0.0', debug=False, threaded=True, **self.website_params)
