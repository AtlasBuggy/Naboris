from flask import Flask, render_template
from atlasbuggy.datastream import DataStream

class Website(DataStream):
    def __init__(self, template_folder, enabled=True, debug=False, name=None, **website_params):
        self.app = Flask(__name__, template_folder=template_folder)
        self.app.add_url_rule("/", "index", self.index)
        self.website_params = website_params

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
