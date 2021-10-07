import signal, os
import requests
from requests.exceptions import ConnectionError
import time
import subprocess
import sys

start_cmd = 'sudo nohup python3 site.py'
base_cmd = 'python3 site.py'
ps_cmd = 'ps ax | grep site.py'


def exit_handler(signum, frame):
    pid = get_ps(start_cmd)
    print("Exiting process...")
    if pid is not None:
        kill_ps(pid)
        print(f"\t Killed child [{pid}]")
    pid = get_ps(base_cmd)
    if pid is not None:
        kill_ps(pid)
    sys.exit(0)


def get_ps(cmd):
    output = os.popen(cmd).read()
    lines = output.split('\n')
    for line in lines:
        items = line.strip().split(' ')
        items = [i for i in items if i != '']
        start_arr = start_cmd.split(' ')
        start_size = len(start_arr)
        if len(items) > 0 and all([x==y for x,y in zip(start_arr, items[start_size:])]):
            return int(items[0])
    return None
        

def kill_ps(pid):
    os.kill(int(pid), signal.SIGKILL)
    #os.system(f'sudo kill -15 {pid}')
    #print(f"Killed {pid}")
    return True


def ping_site():
    print("Pinging site...")
    try:
        res = requests.get('https://www.bensonea.com/', 
                timeout=5,
                verify=False)
        return True
    except Exception as e:
        print(e)
        return False


def start_server():
    print("Starting site...")
    x = subprocess.Popen(f"{start_cmd} &", shell=True)
    pid = get_ps(start_cmd)
    print(f"\tSite pid: {pid}")
    if pid is not None:
        return pid
    return None


def run_site():
    start_server()
    pid = get_ps(start_cmd)
    while True:
        time.sleep(5)
        if not ping_site():
            kill_ps(pid)
            pid = start_server()

signal.signal(signal.SIGTERM, exit_handler)

run_site()
