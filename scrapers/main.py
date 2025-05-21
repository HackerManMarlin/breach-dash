import yaml, pathlib, importlib, os, sys, croniter, datetime as dt

CFG = yaml.safe_load(open(pathlib.Path(__file__).parent/'config.yaml'))
for pid, portal in CFG.items():
    portal["id"] = pid

def run_due_portals():
    now = dt.datetime.utcnow()
    print(f"Starting portal check at Current time: {now}") # Added a start log

    for portal in CFG.values():
        # Determine the most recent past or current schedule time for this portal
        iter_for_schedule_slot = croniter.croniter(portal["schedule"], now)
        current_slot_start_time = iter_for_schedule_slot.get_prev(dt.datetime)

        # For logging, determine when this slot notionally ends (i.e., when the next one begins)
        iter_for_next_slot = croniter.croniter(portal["schedule"], current_slot_start_time)
        next_slot_start_time = iter_for_next_slot.get_next(dt.datetime)

        print(f"Portal: {portal['id']} (Schedule: {portal['schedule']}) - Current time: {now}. Identified slot: [{current_slot_start_time}, {next_slot_start_time})")

        # Condition: Run if 'now' is at or after the start of this identified slot.
        # This means 'now' falls within the execution window that began at 'current_slot_start_time'.
        if now >= current_slot_start_time:
            print(f"==> Running portal: {portal['id']} (for slot starting {current_slot_start_time})")
            try:
                mod = importlib.import_module(f"scrapers.fetch_{portal['type']}")
                mod.run(portal)
                print(f"<== Finished portal: {portal['id']}")
            except Exception as e:
                print(f"[ERROR] Failed running portal {portal['id']}: {e}")
        else:
            # This case should be very rare given get_prev() logic, but included for completeness.
            print(f"--> Not due (should be rare): {portal['id']}. Current time {now} is somehow before its calculated slot start {current_slot_start_time}.")

if __name__ == "__main__":
    run_due_portals()
