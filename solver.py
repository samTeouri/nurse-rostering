from docplex.mp.model import Model

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
    for c in cover:
        model.add_constraint(model.sum(x[e, c["day"], c["shift"]] for e in staff) + y_min[c["day"], c["shift"]] >= c["requirement"], f"cover_min_{c['day']}_{c['shift']}")
        model.add_constraint(model.sum(x[e, c["day"], c["shift"]] for e in staff) - y_max[c["day"], c["shift"]] <= c["requirement"], f"cover_max_{c['day']}_{c['shift']}")

    # 4. Contraintes sur le nombre total d'heures travaillées
    for e in staff:
        min_hours = int(staff[e]["constraints"][2])  # tmin
        max_hours = int(staff[e]["constraints"][1])  # tmax
        total_hours = model.sum(x[e, d, s] * int(shifts[s]["duration"]) for d in range(horizon) for s in shifts)
        model.add_constraint(total_hours >= min_hours, f"min_hours_{e}")
        model.add_constraint(total_hours <= max_hours, f"max_hours_{e}")

    # 5. Contraintes sur le nombre de jours consécutifs qu'un employé ne peux travailler
    for e in staff:
        max_consec = int(staff[e]["constraints"][3])  # cmax
        for d in range(horizon - max_consec + 1):
            model.add_constraint(
                model.sum(x[e, d + k, s] for k in range(max_consec) for s in shifts) <= max_consec,
                f"max_consecutive_{e}_{d}"
            )
    
    # 6. Contraintes sur le nombre de jours consécutifs qu'un employé doit travailler
    # for e in staff:
    #     min_consec = int(staff[e]["constraints"][4])  # cmin
    #     for d in range(horizon - min_consec + 1):
    #         model.add_constraint(
    #             model.sum(x[e, d + k, s] for k in range(min_consec) for s in shifts) >= min_consec,
    #             f"min_consecutive_{e}_{d}"
    #         )

    # 7. Contraintes sur le nombre minimum de jours de repos consécutifs qu'un employé doit avoir
    # for e in staff:
    #     min_rest = int(staff[e]["constraints"][5])  # rmin
    #     for d in range(horizon - min_rest + 1):
    #         model.add_constraint(
    #             model.sum(1 - model.sum(x[e, d + k, s] for s in shifts) for k in range(min_rest)) >= min_rest,
    #             f"min_rest_{e}_{d}"
    #         )

    # 8. Contraintes sur le nombre maximum de week-ends qu'un employé ne peut travailler
    for e in staff:
        max_weekends = int(staff[e]["constraints"][6])  # wmax
        weekends_worked = model.sum(
            x[e, d, s] for d in range(horizon) if d % 7 in [5, 6] for s in shifts  # Samedi et dimanche
        )
        model.add_constraint(weekends_worked <= max_weekends, f"max_weekends_{e}")

    # Objective function
    penalty = model.sum(
        i["weight"] * (1 - x[i["employee"], i["day"], i["shift"]]) for i in shift_on_requests
    ) + model.sum(
        i["weight"] * x[i["employee"], i["day"], i["shift"]] for i in shift_off_requests
    ) + model.sum(
        y_min[d, s] * cover[d]["under_penalty"] + y_max[d, s] * cover[d]["over_penalty"] for d, s in y_min
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
    return None
