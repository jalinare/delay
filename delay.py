#!/usr/bin/python

import re
import socket
import argparse

from csr_aws_guestshell import cag

class CSR1000V(cag):
    def send_delay_metric(self, name, value, category, target):
        value = int(value)
        response = self.cloudwatch.put_metric_data(
            Namespace="csr1000v",
            MetricData=[{'MetricName': name,
                         'Value': value,
                         'Unit': 'Count',
                         'Dimensions': [
                             {
                                 "Name": "InstanceId",
                                 "Value": self.instance_id
                             },
                             {
                                 "Name": "Target",
                                 "Value": target
                             }
                         ],
                         }
                        ],
        )
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            print "Error sending %s" % name

csr = CSR1000V()
    
def print_cmd_output(command, output, print_output):
    if print_output:
        col_space = (80 - (len(command))) / 2
        print "\n%s %s %s" % ('=' * col_space, command, '=' * col_space)
        print "%s \n%s" % (output, '=' * 80)

def execute_command(command, print_output):
    cmd_output = cli.execute(command)
    #'Type escape sequence to abort.\nSending 5, 100-byte ICMP Echos to 128.150.248.10, timeout is 2 seconds:\n!!!!!\nSuccess rate is 100 percent (5/5), round-trip min/avg/max = 1/1/2 ms'
    
    while len(cmd_output) == 0:
        print "CMD FAILED, retrying"
        cmd_output = cli.execute(command)

    print_cmd_output(command, cmd_output, print_output)
    return cmd_output

def round_trip_time(addr, print_output):
    cmd_output = execute_command("ping " + addr, print_output)
    m = re.search(r'min/avg/max = (\d+)/(\d+)/(\d+)', cmd_output)
    if m:
        # print m.group(1)
        csr.send_delay_metric("min", m.group(1), "Minimum delay", addr)
        # print m.group(2)
        csr.send_delay_metric("avg", m.group(2), "Average delay", addr)
        # print m.group(3)
        csr.send_delay_metric("max", m.group(3), "Maximum delay", addr)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload delay stats to custom metrics")
    parser.add_argument('-d', '--display', help='show output', action='store_true')
    parser.add_argument('addr', help='Specify target IP to measure delay')
    args = parser.parse_args()
    
    try:
        socket.inet_aton(args.addr)
        round_trip_time(args.addr, args.display)
    except socket.error: 
        print "Invalid address"