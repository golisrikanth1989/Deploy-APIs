# type = "gnb-epc"
# request(
#   software_release = "https://lab.nexedi.com/nexedi/slapos/raw/1.0.308/software/ors-amarisoft/software-tdd3700.cfg",
#   partition_reference = "ors17-nr",
#   software_type = "gnb-epc",
#   filter_kw = { 'computer_guid': "COMP-3517"},
#   partition_parameter_kw = {'_': '{"tx_gain": 50, "rx_gain": 40}'},
#   state = "started"
# )

import json
epc_plmn = "00101"
tx_gain = 80
nr_band = 78
dl_nr_arfcn = 519000
obj = {"epc_plmn": epc_plmn, "tx_gain": tx_gain, "rx_gain": 35, "dl_nr_arfcn": dl_nr_arfcn, "nr_band": nr_band, "use_ipv4": True}
state1 = "started"


result = json.dumps(obj)
print(type(obj))
print(type(result))

ret = request(software_release = "https://lab.nexedi.com/nexedi/slapos/raw/1.0.308/software/ors-amarisoft/software-tdd3700.cfg",
              partition_reference = "ors17-nr",
              software_type = "gnb-epc",
              filter_kw = { 'computer_guid' : "COMP-3517" },
              partition_parameter_kw = {"_": result} ,
              state = state1)

print(ret.getState())
print(ret.getConnectionParameterDict())
print(ret.getInstanceParameterDict())
print("done")