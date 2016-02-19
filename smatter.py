import tornado.ioloop
import tornado.web
import tornado.websocket
import json
from opengraph import OpenGraph
from pymongo import MongoClient

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        items = ["Item 1", "Item 2", "Item 3"]
        self.render("content.html", title="My title", items=items)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", EchoWebSocket),
    ])

class EchoWebSocket(tornado.websocket.WebSocketHandler):
    CONNECTIONS = set()
    def open(self):
        self.CONNECTIONS.add(self)
        mc = MongoClient()
        stories = []
        for i in mc.matter.smatter.find():
            i.pop('_id')
            stories.append(i)
        self.write_message(json.dumps(stories))
        print("WebSocket opened")

    def on_message(self, message):
        val = json.loads(message)
        if val.get('type') == 'sub':
            mc = MongoClient()
            og = OpenGraph(url=val.get('value'))
            ret = {'type':'submission', 'url': og.url, 'image': og.image, 'type': og.type, 'description': og.description, 'title': og.title }
            self.write_message(json.dumps(ret))
            mc.matter.smatter.insert_one(ret)
        elif val.get('type') == 'msg':
            for i in self.CONNECTIONS:
                if i != self:
                    i.write_message('{"type":"msg", "values":" '+ val.get('value') + '"}')
        elif val.get('type') == 'typing':
            for i in self.CONNECTIONS:
                if i != self:
                    i.write_message('{"type":"typing", "values": "A user is typing something..."}')
    def on_close(self):
        self.CONNECTIONS.remove(self)
        print("WebSocket closed")


if __name__ == "__main__":
    app = make_app()
    app.listen(80)
    tornado.ioloop.IOLoop.current().start()