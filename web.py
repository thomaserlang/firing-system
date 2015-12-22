import logging
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.websocket
import math
import os
import json
import constants
from decorators import new_cursor

class Web_handler(tornado.web.RequestHandler):

    def get(self):
        self.render(
            'ports.html',
            GROUPED_PORTS=constants.GROUPED_PORTS,
            CONNECTIONS_PER_PORT=constants.CONNECTIONS_PER_PORT,
            PORT_COLORS=constants.PORT_COLORS,
            groups=self.groups(),
            selected_group=self.selected_group(),
            ports=json.dumps(self.ports()),
        )

    def ports(self):
        group_id = self.get_argument('group_id', None)
        if not group_id:
            return []
        with new_cursor() as c:
            rows = c.execute(
                'SELECT * FROM ports WHERE group_id=?',
                (group_id,)
            ).fetchall()
            data = []
            for row in rows:
                data.append({
                    'port': row['port'],
                    'connection': row['connection'],
                    'enabled': True if row['enabled'] == 'Y' else False,
                    'delay': row['delay'],
                })
            return data

    def selected_group(self):
        group_id = self.get_argument('group_id', None)
        if not group_id:
            return
        return self.group_by_id(group_id)

    def group_by_id(self, group_id):
        with new_cursor() as c:         
            return c.execute(
                'SELECT * FROM groups WHERE id=?',
                (group_id,)
            ).fetchone()

    def parse_delay(self, delay):
        if not delay:
            return 0
        try:
            return int(delay)
        except ValueError:
            return 0

    def post(self):
        name = self.get_argument('groupname')
        if not name:
            self.redirect('/')
            return
        with new_cursor() as c:
            group = c.execute(
                'SELECT * FROM groups WHERE name=?;', (name,)
            ).fetchone()
            if group:
                group_id = group['id']
            else:
                c.execute('INSERT INTO groups (name) VALUES (?);', (name,))
                group_id = c.lastrowid
            data = json.loads(self.get_argument('json'))
            pdata = []
            for d in data:
                pdata.append(
                    (
                        group_id, 
                        d['port'], 
                        d['connection'], 
                        'Y' if d['enabled'] else 'N',
                        self.parse_delay(d['delay']),
                    )
                )
            c.execute('DELETE FROM ports WHERE group_id=?;', (group_id,))
            c.executemany(
                '''
                    INSERT INTO ports 
                        (group_id, port, connection, enabled, delay) 
                    VALUES 
                        (?, ?, ?, ?, ?)
                ''',
                pdata
            )
            self.redirect('/?group_id={}'.format(group_id))
            return

    def groups(self):
        with new_cursor() as c:
            return c.execute(
                'SELECT * FROM groups ORDER BY name ASC;'
            ).fetchall();

class Firing_progress_handler(tornado.websocket.WebSocketHandler):

    clients = []

    @classmethod
    def send_message(cls, message):
        for c in cls.clients:
            c.write_message(message)

    def open(self):
        Firing_progress_handler.clients.append(self)

    def on_message(self, message):
        pass

    def on_close(self):
        Firing_progress_handler.clients.remove(self)

class Fire_handler(tornado.web.RequestHandler):

    t = None

    def get(self):
        pass

    def post(self):
        import threading
        import fire
        cancel = self.get_argument('cancel', None)
        if cancel:
            fire.stop = True
            return
        if Fire_handler.t:
            if Fire_handler.t.isAlive():
                return
        Fire_handler.t = threading.Thread(
            target=fire.fire, 
            args=(self.get_argument('group_id')),
        )
        fire.stop = False
        Fire_handler.t.daemon = True
        Fire_handler.t.start()

def main():
    con = init_db(constants.DATABASE_FILE)
    application = tornado.web.Application(
        [
            (r'/', Web_handler),
            (r'/firing-progress', Firing_progress_handler),
            (r'/fire', Fire_handler),
        ], 
        debug=True, 
        xsrf_cookies=False,
        autoescape=None,
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
    )
    application.listen(8000)
    tornado.options.parse_command_line()
    tornado.ioloop.IOLoop.instance().start()

def init_db(db_file):
    with new_cursor() as c:
        c.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY,
                name TEXT
            );
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS ports (
                group_id INT NOT NULL,
                port INT NOT NULL,
                connection INT NOT NULL,
                enabled TEXT,
                delay INT DEFAULT 0,
                PRIMARY KEY (group_id, port, connection)
            );
        ''')

if __name__ == '__main__':
    main()