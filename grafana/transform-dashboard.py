import json, sys, os

datasource_id = os.getenv("DATASOURCE_ID")

def replace_uid_in_datasource(obj):
    if isinstance(obj, dict):
        # check if this dict has a "datasource" key
        for key, value in obj.items():
            if key == "datasource" and isinstance(value, dict):
                # replace all "uid" values inside this "datasource" dict
                for k in value:
                    if k == "uid":
                        value[k] = datasource_id
            else:
                # recursive call
                replace_uid_in_datasource(value)
    elif isinstance(obj, list):
        for item in obj:
            replace_uid_in_datasource(item)

input = sys.stdin.read()
d = json.loads(input)

d['id'] = None
replace_uid_in_datasource(d)
d = { "dashboard": d, "overwrite": True }

sys.stdout.write(json.dumps(d, indent = 2))
