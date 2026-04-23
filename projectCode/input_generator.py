import sys
import os
import random

def generate_random_garage_state():

    # 1. RANDOMIZE MECHANICS

    num_mechanics = random.randint(3, 10)
    # List of tuples: (Mechanic_ID, Fatigue_Limit_k between 2 and 6)
    mechanics = [(i, random.randint(2, 6)) for i in range(1, num_mechanics + 1)]

    # 2. RANDOMIZE CAR TYPES (DAG BLUEPRINTS)

    num_car_types = random.randint(4, 6)
    car_types = {}
    
    for type_id in range(1, num_car_types + 1):
        total_tasks = random.randint(2, 6)  # Number of baseline tasks for this car type
        edges = []
        
        # Guarantee at least one valid path for every node (except the first)
        # to ensure the DAG isn't just floating, disconnected tasks.
        for j in range(2, total_tasks + 1):
            i = random.randint(1, j - 1)  # Strictly point from lower ID to higher ID
            prob = round(random.uniform(0.0, 0.6), 2) # Keep probability between 0% and 60%
            edges.append((i, j, prob))
            
        # Add a 30% chance for extra, complex cross-dependencies
        for i in range(1, total_tasks):
            for j in range(i + 2, total_tasks + 1):
                if random.random() < 0.30:
                    prob = round(random.uniform(0.0, 0.4), 2)
                    edges.append((i, j, prob))
        
        # Remove any duplicate edges created by the randomizer
        unique_edges = list(set(edges))
        # Sort edges for cleaner reading in the text file
        unique_edges.sort(key=lambda x: (x[0], x[1]))
        
        car_types[type_id] = {
            "total_tasks": total_tasks,
            "edges": unique_edges
        }

    # 3. RANDOMIZE DAILY QUEUE (GUARANTEE >= 10 CARS)
    
    daily_queue_dict = {t_id: 0 for t_id in car_types.keys()}
    total_cars = 0
    
    # Keep adding random batches of cars until we hit the threshold
    while total_cars < 10:
        for type_id in car_types.keys():
            added_qty = random.randint(0, 3)
            daily_queue_dict[type_id] += added_qty
            total_cars += added_qty
            
    # Convert dict to the expected list of tuples
    daily_queue = [(k, v) for k, v in daily_queue_dict.items() if v > 0]

    return mechanics, car_types, daily_queue


def build_output_string(mechanics, car_types, daily_queue):
    output_lines = []

    output_lines.append("% --- MECHANICS ---")
    output_lines.append("% Format: M <MechanicID> <FatigueLimit_k>")
    for mech_id, k in mechanics:
        output_lines.append(f"M {mech_id} {k}")
    
    output_lines.append("\n% --- CAR TYPE DEFINITIONS (The DAGs) ---")
    output_lines.append("% Format for defining a car: T <CarTypeID> <TotalBaselineTasks>")
    output_lines.append("% Format for defining dependencies: E <CarTypeID> <FromTaskNode> <ToTaskNode> <SpawnProbability>")
    
    for car_id, data in car_types.items():
        output_lines.append(f"\nT {car_id} {data['total_tasks']}")
        for edge in data["edges"]:
            output_lines.append(f"E {car_id} {edge[0]} {edge[1]} {edge[2]:.2f}")

    output_lines.append("\n% --- DAILY QUEUE (Today's Workload) ---")
    output_lines.append("% Format: N <CarTypeID> <Quantity>")
    for car_id, quantity in daily_queue:
        output_lines.append(f"N {car_id} {quantity}")

    return "\n".join(output_lines)


def main():
    # Check for command line argument 'n'
    if len(sys.argv) < 2:
        print("Usage: python input_generator.py <number_of_files>")
        print("Example: python input_generator.py 5")
        sys.exit(1)
        
    try:
        n = int(sys.argv[1])
        if n <= 0:
            raise ValueError
    except ValueError:
        print("[ERROR] Please provide a valid positive integer for the number of files.")
        sys.exit(1)

    print("---------------------------------------------------")
    print(f" Generating {n} random input files for the Garage Scheduling Problem...")
    print("---------------------------------------------------\n")

    for i in range(1, n + 1):
        # 1. Generate unique state
        mechanics, car_types, daily_queue = generate_random_garage_state()
        file_content = build_output_string(mechanics, car_types, daily_queue)
        
        # 2. Format filename with leading zeros (e.g., garage_input_01.txt)
        output_filename = f"garage_input_{i:02d}.txt"
        
        # 3. Write to File
        try:
            with open(output_filename, "w") as file:
                file.write(file_content)
            print(f"Success, created {output_filename}")
        except IOError as e:
            print(f"Error, Failed to write {output_filename}: {e}")

    print("\n----------------------------------------------------")
    print(" Input file generation complete.\n Check the current directory for the generated files.")
    print("-----------------------------------------------------")

if __name__ == "__main__":
    main()