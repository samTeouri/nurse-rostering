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
