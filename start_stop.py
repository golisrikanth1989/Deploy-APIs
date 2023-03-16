
import sys

for i in range(1, len(sys.argv)):
    print('argument:', i, 'value:', sys.argv[i])
type = "gnb-epc"
request(
  software_release = "https://lab.nexedi.com/nexedi/slapos/raw/1.0.308/software/ors-amarisoft/software-tdd3700.cfg",
  partition_reference = "ors17-nr",
  software_type = type,
  filter_kw = { 'computer_guid': "HOSTSUBS-52670"},
  partition_parameter_kw = {'_': '{"tx_gain": 50, "rx_gain": 40}'}
)