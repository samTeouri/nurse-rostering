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


    # 5. Contraintes sur les jours de travail consécutifs
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
