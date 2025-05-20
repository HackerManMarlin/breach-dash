import yaml, pathlib, importlib, os, sys, croniter, datetime as dt

CFG = yaml.safe_load(open(pathlib.Path(__file__).parent/'config.yaml'))
for pid, portal in CFG.items():
    portal["id"] = pid

def run_due_portals():
    now = dt.datetime.utcnow()
    for portal in CFG.values():
        itr = croniter.croniter(portal["schedule"], now - dt.timedelta(minutes=1))
        if itr.get_next(dt.datetime) <= now:
            mod = importlib.import_module(f"scrapers.fetch_{portal['type']}")
            mod.run(portal)

if __name__ == "__main__":
    run_due_portals()
