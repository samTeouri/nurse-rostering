from docplex.mp.model import Model

def solve_nurse_rostering(data):

    # Création du modèle
    model = Model(name="Nurse Rostering")

    # Chargement des données depuis `data`
    horizon = data["horizon"]
    shifts = data["shifts"]
    staff = data["staff"]
    days_off = data["days_off"]
    shift_on_requests = data["shift_on_requests"]
    shift_off_requests = data["shift_off_requests"]
    cover = data["cover"]

    # Variables de décision
    x = model.binary_var_dict(
        ((e, d, s) for e in staff for d in range(horizon) for s in shifts),
        name="x"
    )
    y_min = model.integer_var_dict(
        ((d, s) for d in range(horizon) for s in shifts),
        name="y_min"
    )
    y_max = model.integer_var_dict(
        ((d, s) for d in range(horizon) for s in shifts),
        name="y_max"
    )

    # Contraintes

    # 1. Un employé ne peut travailler qu'un seul poste par jour
    for e in staff:
        for d in range(horizon):
            model.add_constraint(model.sum(x[e, d, s] for s in shifts) <= 1, f"one_shift_per_day_{e}_{d}")

    # 2. Contraintes sur les jours de repos
    for e, days in days_off.items():
        for d in days:
            model.add_constraint(model.sum(x[e, d, s] for s in shifts) == 0, f"days_off_{e}_{d}")

    # 3. Couverture des postes
    for d, s, req, _, _ in cover:
        model.add_constraint(model.sum(x[e, d, s] for e in staff) + y_min[d, s] >= req, f"cover_min_{d}_{s}")
        model.add_constraint(model.sum(x[e, d, s] for e in staff) - y_max[d, s] <= req, f"cover_max_{d}_{s}")

    # 4. Contraintes sur le nombre total d'heures travaillées
    for e in staff:
        min_hours = int(staff[e]["constraints"][2])  # tmin
        max_hours = int(staff[e]["constraints"][1])  # tmax
        total_hours = model.sum(x[e, d, s] * int(shifts[s]["duration"]) for d in range(horizon) for s in shifts)
        model.add_constraint(total_hours >= min_hours, f"min_hours_{e}")
        model.add_constraint(total_hours <= max_hours, f"max_hours_{e}")


    # 5 et 6. Contraintes sur les jours de travail consécutifs
    for e in staff:
        min_consec = int(staff[e]["constraints"][4])
        max_consec = int(staff[e]["constraints"][3])
        for d in range(horizon - min_consec + 1):
            model.add_constraint(
                model.sum(x[e, d + k, s] for k in range(min_consec) for s in shifts) >= min_consec,
                f"min_consec_{e}_{d}"
            )
        for d in range(horizon - max_consec + 1):
            model.add_constraint(
                model.sum(x[e, d + k, s] for k in range(max_consec) for s in shifts) <= max_consec,
                f"max_consec_{e}_{d}"
            )

    # Objective function
    penalty = model.sum(
        w * (1 - x[e, d, s]) for e, d, s, w in shift_on_requests
    ) + model.sum(
        w * x[e, d, s] for e, d, s, w in shift_off_requests
    ) + model.sum(
        y_min[d, s] * cover[d][3] + y_max[d, s] * cover[d][4] for d, s in y_min
    )
    model.minimize(penalty)

    # Resolution
    solution = model.solve(log_output=True)

    # Results
    if solution:
        print("Solution trouvée avec un coût total de :", solution.objective_value)
        assignments = [
            (e, d, s) for e in staff for d in range(horizon) for s in shifts if x[e, d, s].solution_value > 0.5
        ]
        return assignments
    print("Pas de solution trouvée.")
    return None

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
