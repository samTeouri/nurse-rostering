def load_instance(file_path):
    """Function to load data from the instance"""
    data = {
        "horizon": 0,
        "shifts": {},
        "staff": {},
        "days_off": {},
        "shift_on_requests": [],
        "shift_off_requests": [],
        "cover": []
    }

    with open(file_path, 'r') as file:
        lines = file.readlines()

    current_section = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):  # Ignore empty lines and comments
            continue

        if line.startswith("SECTION_"):
            current_section = line
            continue

        parts = line.split(',')
        if current_section == "SECTION_HORIZON":
            if line.isdigit():
                data["horizon"] = int(line)
        elif current_section == "SECTION_SHIFTS":
            shift_id, duration, *incompatible_shifts = parts
            data["shifts"][shift_id] = {
                "duration": int(duration),
                "incompatible": incompatible_shifts[0].split('|') if incompatible_shifts else []
            }
        elif current_section == "SECTION_STAFF":
            staff_id, constraints = parts[0], parts[1:]
            data["staff"][staff_id] = {
                "constraints": constraints
            }
        elif current_section == "SECTION_DAYS_OFF":
            employee, *days = parts
            data["days_off"][employee] = list(map(int, days))
        elif current_section == "SECTION_SHIFT_ON_REQUESTS":
            employee, day, shift_id, weight = parts
            data["shift_on_requests"].append({
                "employee": employee,
                "day": int(day),
                "shift": shift_id,
                "weight": int(weight)
            })
        elif current_section == "SECTION_SHIFT_OFF_REQUESTS":
            employee, day, shift_id, weight = parts
            data["shift_off_requests"].append({
                "employee": employee,
                "day": int(day),
                "shift": shift_id,
                "weight": int(weight)
            })
        elif current_section == "SECTION_COVER":
            day, shift_id, requirement, under_penalty, over_penalty = parts
            data["cover"].append({
                "day": int(day),
                "shift": shift_id,
                "requirement": int(requirement),
                "under_penalty": int(under_penalty),
                "over_penalty": int(over_penalty)
            })

    return data
