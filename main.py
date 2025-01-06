# import os
# import sys
# from time import time
# from solver import load_instance, solve_nurse_rostering, save_solution_to_ros

# # Vérifier les arguments
# if len(sys.argv) < 2:
#     print("Usage : python main.py <chemin_instance>")
#     exit(1)

# instance_path = sys.argv[1]

# # Vérifier si le fichier existe
# if not os.path.exists(instance_path):
#     print(f"Erreur : Le fichier '{instance_path}' est introuvable.")
#     exit(1)

# # Charger l'instance
# try:
#     data = load_instance(instance_path)
# except Exception as e:
#     print(f"Erreur lors du chargement de l'instance : {e}")
#     exit(1)

# # Résoudre le problème
# start_time = time()
# solution = solve_nurse_rostering(data)
# end_time = time()

# # Afficher les résultats
# if solution:
#     print(f"Solution trouvée en {end_time - start_time:.2f} secondes.")
#     save_solution_to_ros("solution.ros", solution)
#     print("Assignations :")
#     for e, d, s in solution:
#         print(f"Employé {e} travaille au poste {s} le jour {d}")
# else:
#     print("Aucune solution trouvée.")


import sys
from solver import load_instance, solve_nurse_rostering

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <instance_file>")
        return

    instance_file = sys.argv[1]

    try:
        instance_data = load_instance(instance_file)
    except FileNotFoundError:
        print(f"Error: File {instance_file} not found.")
        return

    objective_value = solve_nurse_rostering(instance_data)

    if objective_value is not None:
        print("Solution trouvée")
    else:
        print("Aucune solution trouvée.")

if __name__ == "__main__":
    main()