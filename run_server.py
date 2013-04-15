from util import server, rsutil

if __name__ == "__main__":
    rsutil.rdnd()
    s = server.DSServer()
    rsutil.rdnd()
    s.serve_forever()