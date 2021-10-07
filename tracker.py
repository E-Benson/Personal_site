import geoip2.database
import json

outfile = './tracker/connections.txt'
db = geoip2.database.Reader('./tracker/geoip.mmdb')
history = dict()
site = "https://www.bensonea.com/"

def clean_request(req):
    size = len(site)-1
    return req[size:]

def get_country(ip):
    res = db.country(ip)
    return res.country.name

def load_history():
    global history
    with open(outfile, 'r') as f:
        history = json.loads(f.read())

def save_history():
    global history
    with open(outfile, 'w') as f:
        f.write(json.dumps(history))

def new_connection(ip, req):
    global history
    ctry = get_country(ip)
    history[ip] = (ctry, [clean_request(req)])

def lookup_ip(ip):
    try:
        return history[ip]
    except KeyError as e:
        return None

def log_ip(ip, req):
    _id = lookup_ip(ip)
    if not _id:
        new_connection(ip, req)
    else:
        request_history = _id[1]
        request_history.append(clean_request(req))
    save_history()
        
def print_history():
    global history
    for ip in history.keys():
        ctry = history[ip][0]
        print("{0:<16}  {1:<20}".format(ip, ctry))
        #print(f"\t{history[ip][1]}")
        request_history = history[ip][1]
        for req in request_history[-5:]:
            print(f"\t{req}")
        print("")

load_history()
if __name__ == "__main__":
    print_history()
else:
    pass

