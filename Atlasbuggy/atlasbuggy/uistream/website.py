from atlasbuggy.uistream import UIstream


class Website(UIstream):
    def __init__(self, name, debug, app):
        super(Website, self).__init__(name, debug)
        self.app = app

    async def run(self):
        await self.app.run(host='0.0.0.0', debug=True, threaded=True)
