#!/usr/bin/env python3
import redis
import json
import time
import shlex, os
import argparse
from subprocess import PIPE, Popen

def process_message(msg):
    return # should be commented if we want to see the allocated time by the processor
    if msg is None:
        return
    counter = 0
    for char in msg:
        counter += 1
    return msg

def bench(sn, sp, c, pipe=False, cli=False, lrangetrick=False, redis_proto_algo=1, d=1000):
    generate_redis_proto_dico = {
            0: no_gene_redis_proto,
            1: generate_redis_proto_format,
            2: generate_redis_proto_concat,
            3: generate_redis_proto_subst
    }
    tpush=tpop=cpush=cpop=0
    lrangeC = 100
    if pipe:
        for i in range(int(c/d)):
            t1=time.time()
            for j in range(d):
                sp.lpush('k', payload)
                cpush+=1
            sp.execute()
            tpush += time.time()-t1
            t1=time.time()
            if not lrangetrick:
                for j in range(d):
                    sp.rpop('k')
                resp = sp.execute()
                for rep in resp:
                    process_message(rep)
                    cpop+=1
            else:
                for j in range(int(d/lrangeC)):
                    resp = sn.lrange('k', -lrangeC, -1)
                    sn.ltrim('k', 0, -len(resp)-1)
                    for rep in resp:
                        process_message(rep)
                        cpop+=1
            tpop += time.time()-t1

    elif cli:
        g_proto = generate_redis_proto_dico[redis_proto_algo]
        for i in range(int(c/d)):
            t1=time.time()
            for j in range(d):
                w(g_proto('lpush', 'k', payload))
                cpush+=1
            tpush += time.time()-t1
            t1=time.time()
            if not lrangetrick:
                for j in range(d):
                    sp.rpop('k')
                resp = sp.execute()
                for rep in resp:
                    process_message(rep)
                    cpop+=1
            else:
                for j in range(int(d/lrangeC)):
                    resp = sn.lrange('k', -lrangeC, -1)
                    sn.ltrim('k', 0, -len(resp)-1)
                    for rep in resp:
                        process_message(rep)
                        cpop+=1
            tpop += time.time()-t1

        # closing so that we push remaining buffered items
        cli_pipe.stdin.close()
        cli_pipe.wait()

        # finish poping remaining items
        t1=time.time()
        while cpop!=cpush:
            resp = sn.lrange('k', -lrangeC, -1)
            sn.ltrim('k', 0, -len(resp)-1)
            for rep in resp:
                cpop+=1
                process_message(rep)
        tpop += time.time()-t1

    else:
        for i in range(int(c/d)):
            t1=time.time()
            for j in range(d):
                sn.lpush('k', payload)
                cpush+=1
            tpush += time.time()-t1
            t1=time.time()
            if not lrangetrick:
                for j in range(d):
                    rep = sn.rpop('k')
                    process_message(rep)
                    cpop+=1
            else:
                for j in range(int(d/lrangeC)+1):
                    resp = sn.lrange('k', -lrangeC, -1)
                    sn.ltrim('k', 0, -len(resp)-1)
                    for rep in resp:
                        process_message(rep)
                        cpop+=1
            tpop += time.time()-t1

    return {'cpush': cpush, 'time_push': tpush, 'cpop': cpop, 'time_pop': tpop}

def generate_redis_proto_format(cmd, key, value=''):
    cmd_split = cmd.split()
    if value == '':
        proto = '*{argNum}\r\n${argLen1}\r\n{arg1}\r\n${argLen2}\r\n{arg2}\r\n'.format(
                argNum=3 if value != '' else 2,
                argLen1=len(cmd), arg1=cmd,
                argLen2=len(key), arg2=key)
    else:
        proto = '*{argNum}\r\n${argLen1}\r\n{arg1}\r\n${argLen2}\r\n{arg2}\r\n${argLen3}\r\n{arg3}\r\n'.format(
                argNum=3 if value != '' else 2,
                argLen1=len(cmd), arg1=cmd,
                argLen2=len(key), arg2=key,
                argLen3=len(value), arg3=value)
    return proto


def generate_redis_proto_concat(cmd, key, value=''):
    cmd_split = cmd.split()
    proto = '*'+(str(3) if value != '' else str(2))+'\r\n'
    proto += '$'+str(len(cmd))+'\r\n'+cmd+'\r\n'
    proto += '$'+str(len(key))+'\r\n'+key+'\r\n'
    if value != '':
        proto += '$'+str(len(value))+'\r\n'+value+'\r\n'
    return proto

def generate_redis_proto_subst(cmd, key, value=''):
    cmd_split = cmd.split()

    if value != '':
        proto = '*%s\r\n$%s\r\n%s\r\n$%s\r\n%s\r\n$%s\r\n%s\r\n' % ((str(3) if value != '' else str(2)), len(cmd), cmd, len(key), key, len(value), value)
    else:
        proto = '*%s\r\n$%s\r\n%s\r\n$%s\r\n%s\r\n' % ((str(3) if value != '' else str(2)), len(cmd), cmd, len(key), key)
    return proto

def no_gene_redis_proto(cmd, key, value=''):
    proto = '*3\r\n$5\r\nlpush\r\n$1\r\nk\r\n$129\r\n{"origin": null, "channel": 0, "content": "redis@tshark_save:53619abd-a27c-432c-8f8d-1d059aab5f24", "size": 54, "redirect": true}\r\n' 
    return proto


def w(proto_cmd):
    try:
        cli_pipe.stdin.write(proto_cmd)
    except IOError as e:
        return


payload = '{\"origin\": null, \"channel\": 0, \"content\": \"redis@tshark_save:53619abd-a27c-432c-8f8d-1d059aab5f24\", \"size\": 54, \"redirect\": true}'
sockpath = '/tmp/redis_easyFlow_buffers.sock'
r = redis.StrictRedis(unix_socket_path=sockpath, db=1)
p = r.pipeline()
cli_pipe = None

parser = argparse.ArgumentParser(description='Benchmark lpush/rpop.')
parser.add_argument('--pipe', dest='use_pipe', action='store_true',
                    help='Use the pipeline feature')
parser.add_argument('-c', dest='count', action='store', default=100000, type=int,
                    help='Use the pipeline feature')
parser.add_argument('-r', dest='redoCount', action='store', default=10, type=int,
                    help='Number of time to redo the benchmark, so that we can average computation time')
parser.add_argument('--pipecli', dest='use_cli', action='store_true',
                    help='Call redis-cli with pipeline feature and write redis protocol to its stdin')
parser.add_argument('--lrangetrick', dest='lrangetrick', action='store_true',
                    help='Replace RPOP by LRANGE/LTRIM')
parser.add_argument('--redis-proto-algo', dest='redis_proto_algo', action='store', type=int, choices=[0,1,2,3], default=1,
        help='Which protocol should be used to generate the redis protocol used to feed redis-cli. 0: no generation, 1: FORMAT, 2: + operator, 3: string substitution (modulo).')

args_cmdline_cli = shlex.split('/home/sami/git/redis/src/redis-cli -s {} -n 1 --pipe'.format(sockpath))
args = parser.parse_args()

if args.use_cli:
    FNULL = open(os.devnull, 'w')

cpush=tpush=cpop=tpop=0
min_tpush=min_tpop=float('inf')
max_tpush=max_tpop=0
for i in range(args.redoCount):

    if args.use_cli:
        cli_pipe = Popen(args_cmdline_cli, stdin=PIPE, stdout=FNULL, universal_newlines=True)

    print('Running test {}...'.format(i), end='\r', flush=True)
    stat = bench(r, p, args.count, pipe=args.use_pipe, cli=args.use_cli, lrangetrick=args.lrangetrick, redis_proto_algo=args.redis_proto_algo)
    cpush += stat['cpush']
    cpop += stat['cpop']
    tpush += stat['time_push']
    tpop += stat['time_pop']
    #min
    min_tpush = min_tpush if min_tpush < stat['time_push'] else stat['time_push']
    min_tpop = min_tpop if min_tpop < stat['time_pop'] else stat['time_pop']
    #max
    max_tpush = max_tpush if max_tpush > stat['time_push'] else stat['time_push']
    max_tpop = max_tpop if max_tpop > stat['time_pop']else stat['time_pop']

cpush = cpush/10
cpop = cpop/10
tpush = tpush/10
tpop = tpop/10
print((
    'pipeline: {}, pipeline+cli: {}\n'+
    'parser: {}\n'+
    'lrangeTrick: {},\tredis-proto-algo: {}\n'+
    'test ran: {}\n'+
    'LPUSH:\n'+
    'tot_time_taken_worst:\t{:.2f}s,\ttot_time_taken_best:\t{:.2f}s,\ttot_time_taken_avg:{:.2f}s\n'+
    'min: {:.0f} op/sec,\t max: {:.0f} op/sec,\t avg: {:.0f} op/sec \n'+
    'RPOP:\n'+
    'tot_time_taken_worst:\t{:.2f}s,\ttot_time_taken_best:\t{:.2f}s,\ttot_time_taken_avg:{:.2f}s\n'+
    'min: {:.0f} op/sec,\t max: {:.0f} op/sec,\t avg: {:.0f} op/sec \n'
    ).format(
    args.use_pipe, args.use_cli,
    str(type(r.connection_pool.get_connection('')._parser)),
    args.lrangetrick,args.redis_proto_algo,
    args.redoCount,
    max_tpush, min_tpush, tpush, 
    cpush/max_tpush, cpush/min_tpush, cpush/tpush,
    max_tpop, min_tpop, tpop,
    cpop/max_tpop, cpop/min_tpop, cpop/tpop
))


