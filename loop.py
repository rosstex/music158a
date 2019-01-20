from pyechonest import config
from earworm import *
from OSC import OSCServer, OSCClient, OSCBundle

config.ECHO_NEST_API_KEY = "ONW40KX13L8TMKXKF"

import sys, time, os, pickle
from os.path import relpath


def receive_song_choice(addr, tags, args, source):
    directory = args[0]
    _, path = directory.split(":")
    song_path = relpath(path, os.curdir)
    print(song_path)
    try:
        loop_points = load(song_path)
        print("Previously analyzed file: " + str(loop_points))
    except IOError:
        print("New file: running analysis.")
        track = LocalAudioFile(song_path, verbose=True)
        print(track)
        actions = do_work(track, None, max_package=True)
        loop_points = get_loop_points(actions)
        # loop_points = distinct(loop_points)
        for loop in loop_points:
            loop[0], loop[1] = loop[1] * 1000, loop[0] * 1000
    save(song_path, loop_points)
    send(loop_points)


def load(song_path):
    path = "analytics/" + song_path.split(".")[0] + ".loops"
    print("load path: " + str(path))
    loop_points = pickle.load(open(path, "rb"))
    print("loaded successfully")
    return loop_points


def save(song_path, loop_points):
    path = "analytics/" + song_path.split(".")[0] + ".loops"
    print("save path: " + str(path))
    pickle.dump(loop_points, open(path, "wb"))


def get_loop_points(actions):
    loops = []
    for action in actions:
        if isinstance(action, Jump):
            print(action.duration)
            source = action.t1.start + action.t1.duration
            target = action.t2.start + action.t2.duration
            loops.append([source, target])
    return loops

# decided not to use
def distinct(loop_points):
    jump_from = set()
    jump_to = set()
    new_loop_points = []

    for loop in loop_points:
        keep = True
        forward = int(loop[0])
        backward = int(loop[1])
        for i in xrange(-1, 2):
            if ((forward + i) in jump_from) or ((backward + i) in jump_to):
                keep = False
                break
        jump_from.add(forward)
        jump_to.add(backward)
        if keep:
            new_loop_points.append(loop)

    return new_loop_points


def send(loop_points):
    bundle = OSCBundle()
    i = 0
    loop_list = []
    for loop in loop_points:
        bundle.append({'addr': "/loops/" + str(i),
                       'args': [loop]})
        loop_list.append("/loops/" + str(i))
        i += 1
    bundle.append({'addr': "/loop_list", 'args': loop_list})
    client.send(bundle)


def run():
    try:
        print("Connection to Max established! Awaiting song choice.")
        count = 1
        while True:
            time.sleep(0.1)
            if count % 5 == 0:
                print("Alive: " + str(count) + " seconds.")
            count += 1
            server.handle_request()
    except KeyboardInterrupt:
        pass

    server.close()


server = OSCServer(('localhost', 2205))
print("Made server")
server.addMsgHandler("/filename", receive_song_choice)

client = OSCClient()
client.connect(("localhost", 2206))
print("Made client")

if __name__ == '__main__':
    run()
