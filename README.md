# network-monitor
Passive-active monitor

usage: monitor.py [-h] [-l LEVEL] [-i INTERFACE] [-a] [-z] [-f FILE] [-t TIME]

active/passive monitor, that show latency(rtt) and jitter, resuming the
information each second For DEFAULT, only listen in one interface

optional arguments:
  -h, --help            show this help message and exit
  -l LEVEL, --level LEVEL
                        level of log, [info, error, debug, warning]
  -i INTERFACE, --interface INTERFACE
                        in which interface is to the program listen
  -a, --active          Generate a lot of traffic tcp in the interface
  -z, --analyzer        Analize one file generate by pping and defined by -f,
                        --file. DEFAULT: analize the file output.txt
  -f FILE, --file FILE  File to be output the pping or/and to be analyzed
  -t TIME, --time TIME  During how much time is to be listen. If ommit, wait
                        ctrl+c from user to stop.


The default mode is passive.
Use the pping (Passive PING) to read the rtt in the tcp packets captured in the interface defined by -i or by the global variable 'default_interface' in the main script.

In the active mode, in addition to the pping, the ipperf create traffic TCP to the IP receives in -p. The pping receives the informations and this script analyze the results.

In the analyzer mode, neither the pping neither the iperf is execute, and is open and analyzed the default file 'output.txt' or the file in the optional argument -f from command line.

The results received are samples of captured packets separated by periods of 1 second. Each period summarized contains the highest RTT, lowest RTT, mean RTT, total sample, as well as higher Jitter, lower Jitter, Jitter mean.