import re
import os
import argparse
import time
from datetime import datetime


# exec time
start_exec = time.time()

parser = argparse.ArgumentParser(prog='SQL_TRC_TIMER', usage="%(prog)s path [options] -h")
parser.add_argument('--last', type=int,
                    help='diplay result only from last n days(24h) from now, but 0 - returns files since midnight',
                    required=False)
parser.add_argument('--sort', type=str, choices=['time', 'date'],
                    help='sort by elapsed time - [time], or trace date - [date] (also sorted by time)',
                    default='time', required=False)
parser.add_argument('--ela', type=float, help='diplay result with elapsed time >= n', required=False)
parser.add_argument('path', type=str, help='set directory path with sql traces')
parser.add_argument('--ef', action='store_true', help='format elapsed by [.3f]', required=False)
args = parser.parse_args()

trc_directory = args.path
trc_regexp = re.compile("\d{2}-\w{3}-\d{4} \d{2}:\d{2}:\d{2}:\d+")
trc_date_format = "%d-%b-%Y %H:%M:%S:%f"
trc_date_format_print = "%d-%b-%Y %H:%M:%S"
trc_file_extension = ".trc"
format_output = ['[{}]:', '{}', '== {}']

trc_time_dict = {}
if not os.path.isdir(trc_directory):
    print("\nFile is not directory, or not exist {}\n".format(trc_directory))
    exit(1)

dir_walk = os.walk(trc_directory)
for item in dir_walk:
    dir_item = item[0]
    file_list = item[2]
    file_set = (os.path.join(dir_item, trc_file) for trc_file in file_list if trc_file.endswith(trc_file_extension))
    for trc_file in file_set:
        if args.last is not None:
            if args.last == 0:
                midnight = datetime.combine(datetime.today(), datetime.min.time())
                if os.stat(trc_file).st_ctime < time.mktime(midnight.timetuple()):
                    continue
            else:
                if os.stat(trc_file).st_ctime < time.time() - args.last * 86400:
                    continue
        with open(trc_file) as f:
            # that dirty hook, read whole file, and save typle in ram
            # TODO: rewrite with block seek
            whole_file = f.readlines()
            # print('{}{}'.format(whole_file[1], whole_file[-1]))
            try:
                start_time = trc_regexp.search(whole_file[1]).group(0)
                stop_time = trc_regexp.search(whole_file[-1]).group(0)
            except AttributeError:
                print("Wrong file format: {}".format(trc_file))
                continue

            start_time_dt = datetime.strptime(start_time, trc_date_format)
            stop_time_dt = datetime.strptime(stop_time, trc_date_format)
            trc_time_delta = stop_time_dt - start_time_dt
            if args.ela is not None and args.ela >= 0:
                if trc_time_delta.total_seconds() < args.ela:
                    continue
            if args.sort == 'date':
                trc_midnight = datetime.combine(start_time_dt, datetime.min.time())
                trc_time_dict.setdefault(trc_midnight, []).append((trc_time_delta.total_seconds(), start_time_dt,
                                                                   trc_file))
            elif args.sort == 'time':
                trc_time_dict[trc_file] = (trc_time_delta.total_seconds(), start_time_dt)

if args.ef:
    format_output[1] = '{:.3f}'

if args.sort == 'time':
    trc_time_sorted = sorted(trc_time_dict.items(), key=lambda z: z[1][0])
    for x_ts in trc_time_sorted:
        print(' '.join(format_output).format(datetime.strftime(x_ts[1][1], trc_date_format_print), x_ts[1][0], x_ts[0]))
    print('Processed: {} files'.format(len(trc_time_sorted)))
elif args.sort == 'date':
    trc_time_sorted = sorted(trc_time_dict.items())
    f_cnt = 0
    for x_tm in trc_time_sorted:
        for x_ts in sorted(x_tm[1]):
            print(' '.join(format_output).format(datetime.strftime(x_ts[1], trc_date_format_print), x_ts[0], x_ts[2]))
            f_cnt += 1
        print('===')
    print('Processed: {} files'.format(f_cnt))

# exec time
stop_exec = time.time()
delta_exec = stop_exec - start_exec
print('{:.3f}'.format(delta_exec))
