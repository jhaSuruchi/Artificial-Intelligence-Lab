import sys
import random
from collections import defaultdict
import csv

# 1. CORE CLASSES

class DualLogger:
    """Routes print statements to both the terminal and a text, csv file."""
    def __init__(self, filepath):
        self.terminal = sys.stdout
        self.log = open(filepath, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

class Task:
    def __init__(self, t_id, name, car_id):
        self.id = t_id
        self.name = name
        self.car_id = car_id
        self.edges_out = []  # List of tuples: (target_task_id, spawn_probability)
        self.in_degree = 0
        self.depth = 1  # Used for Critical Path heuristic

class Car:
    def __init__(self, c_id, type_id):
        self.id = c_id
        self.type_id = type_id
        self.tasks = {}  # task_id -> Task object
        self.available_tasks = []  # Pool of tasks with 0 in-degree ready to be worked on
        self.completed_tasks = set()
        
    def is_complete(self):
        return len(self.completed_tasks) == len(self.tasks)

class Mechanic:
    def __init__(self, m_id, k):
        self.id = m_id
        self.k = k
        self.consecutive_tasks = 0
        self.status = "IDLE"  # IDLE, WORKING, BREAK
        self.current_task = None
        self.timer = 0  # Time remaining on current task or break

# 2. PARSER & GRAPH BUILDER

def parse_input(filepath):
    mechanics = []
    car_templates = {}
    daily_queue = []

    try:
        with open(filepath, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("%"):
                    continue
                
                parts = line.split()
                identifier = parts[0]

                if identifier == "M":
                    m_id = parts[1]
                    k = int(parts[2])
                    mechanics.append(Mechanic(m_id, k))
                
                elif identifier == "T":
                    type_id = parts[1]
                    total_tasks = int(parts[2])
                    car_templates[type_id] = {
                        "nodes": [str(i) for i in range(1, total_tasks + 1)],
                        "edges": []
                    }
                
                elif identifier == "E":
                    type_id = parts[1]
                    from_node = parts[2]
                    to_node = parts[3]
                    prob = float(parts[4])
                    car_templates[type_id]["edges"].append((from_node, to_node, prob))
                
                elif identifier == "N":
                    type_id = parts[1]
                    qty = int(parts[2])
                    for _ in range(qty):
                        daily_queue.append(type_id)
                        
    except FileNotFoundError:
        print(f"[ERROR] Could not find {filepath}. Please ensure the input file is in the correct location.")
        sys.exit(1)

    return mechanics, car_templates, daily_queue

def build_garage_state(car_templates, daily_queue):
    cars = []
    car_counter = 1
    
    for type_id in daily_queue:
        car_id = f"C{car_counter}"
        car = Car(car_id, type_id)
        
        # Build nodes
        for node_id in car_templates[type_id]["nodes"]:
            car.tasks[node_id] = Task(node_id, f"T{node_id}", car_id)
            
        # Build edges and in-degrees
        for from_node, to_node, prob in car_templates[type_id]["edges"]:
            car.tasks[from_node].edges_out.append((to_node, prob))
            car.tasks[to_node].in_degree += 1
            
        # Calculate initial available tasks
        for task in car.tasks.values():
            if task.in_degree == 0:
                car.available_tasks.append(task)
                
        # Calculate Critical Path Depth (Post-order traversal)
        def calc_depth(t_id):
            task = car.tasks[t_id]
            if not task.edges_out:
                return 1
            max_child_depth = 0
            for child_id, _ in task.edges_out:
                max_child_depth = max(max_child_depth, calc_depth(child_id))
            task.depth = max_child_depth + 1
            return task.depth
            
        for task in car.available_tasks:
            calc_depth(task.id)

        cars.append(car)
        car_counter += 1
        
    return cars

def print_phase1_state(cars):
    print("\n                   PHASE 1: BASELINE GENERATION")
    print("----------------------------------------------------------------------------")
    for car in cars:
        print(f"--- {car.id} (Type {car.type_id}) ---")
        for task_id, task in car.tasks.items():
            print(f"  Task {task.name} | In-Degree: {task.in_degree} | Critical Path Depth: {task.depth}")
        
        initial_ready = [t.name for t in car.available_tasks]
        print(f"  Tasks Ready at T=0: {initial_ready}\n")

# 3. SIMULATION ENGINE

def simulate(mechanics, cars):
    time = 0
    gantt_data = {m.id: [] for m in mechanics}
    print("\n                   PHASE 2: DYNAMIC SIMULATION LOG")
    print("----------------------------------------------------------------------------")

    while any(not car.is_complete() for car in cars):
        
        # 1. Process Completions & Breaks at the start of the tick
        for m in mechanics:
            if m.timer > 0:
                m.timer -= 1
                
            if m.timer == 0:
                if m.status == "WORKING":
                    # Task Finished
                    t = m.current_task
                    car = next(c for c in cars if c.id == t.car_id)
                    car.completed_tasks.add(t.id)
                    print(f"[Time={time}] M{m.id} completes [{car.id}-{t.name}].")
                    
                    # Update Fatigue
                    m.consecutive_tasks += 1
                    if m.consecutive_tasks >= m.k:
                        m.status = "BREAK"
                        m.timer = 1  # 1 time-unit mandatory break
                        m.consecutive_tasks = 0
                        print(f"[Time={time}] M{m.id} reached fatigue limit (k={m.k}). Forced 1-unit break.")
                    else:
                        m.status = "IDLE"

                    # Resolve dependencies & Probabilistic Spawns
                    for child_id, prob in t.edges_out:
                        # Rule: Roll rand > prob to spawn
                        if prob > 0.0:
                            chance = random.random()
                            if chance > prob:
                                spawn_id = f"{t.name}_SUB"
                                # Ensure unique sub-task IDs if multiple spawn
                                while spawn_id in car.tasks:
                                    spawn_id += "X" 
                                
                                new_task = Task(spawn_id, spawn_id, car.id)
                                car.tasks[spawn_id] = new_task
                                car.available_tasks.append(new_task) # Appends to end of task list
                                print(f"[Time={time}] EVENT: Hidden defect on {car.id}! [{spawn_id}] added to DAG.")
                        
                        # Unlock baseline dependencies
                        child = car.tasks[child_id]
                        child.in_degree -= 1
                        if child.in_degree == 0:
                            car.available_tasks.append(child)
                            
                    m.current_task = None
                    
                elif m.status == "BREAK":
                    # Break is over
                    m.status = "IDLE"
                    print(f"[Time={time}] M{m.id} returns from break.")

        # 2. Gather and sort all available tasks globally
        global_pool = []
        for car in cars:
            if not car.is_complete():
                for t in car.available_tasks:
                    if t.id not in car.completed_tasks:
                        global_pool.append(t)
                        
        # Sort tasks by Critical Path Depth (Heuristic 1)
        global_pool.sort(key=lambda x: x.depth, reverse=True)

        # 3. Gather and sort idle mechanics by remaining stamina (Heuristic 4)
        idle_mechanics = [m for m in mechanics if m.status == "IDLE"]
        idle_mechanics.sort(key=lambda m: m.k - m.consecutive_tasks, reverse=True)

        # 4. Assign Tasks
        assigned_tasks = set()
        for m in idle_mechanics:
            for task in global_pool:
                if task not in assigned_tasks:
                    m.status = "WORKING"
                    m.current_task = task
                    m.timer = 1
                    assigned_tasks.add(task)
                    
                    # Remove from car's available pool so it isn't picked up twice
                    car = next(c for c in cars if c.id == task.car_id)
                    car.available_tasks.remove(task)
                    
                    print(f"[Time={time}] M{m.id} starts [{car.id}-{task.name}].")
                    break

        # 5. Record state for Gantt Chart (What is happening during this time block)
        for m in mechanics:
            if m.status == "WORKING":
                gantt_data[m.id].append(f"[{m.current_task.car_id}-{m.current_task.name}]")
            elif m.status == "BREAK":
                gantt_data[m.id].append("[ BREAK ]")
            else:
                gantt_data[m.id].append("[ IDLE  ]")

        # Advance Clock
        time += 1

    print(f"[Time={time}] All tasks complete. Simulation terminated.")
    return time, gantt_data

# 4. OUTPUT GENERATOR

def print_gantt_chart(makespan, mechanics, gantt_data):
    print("\n                   PHASE 2: Final Schedule Gantt Chart")
    print("----------------------------------------------------------------------------")
    print(f"Final Makespan: {makespan} Time Units\n")
    
    # Print Header
    header = "          "
    for t in range(makespan):
        header += f"Time={t:<8}"
    print(header)
    
    # Print Rows
    for m in mechanics:
        row = f"M{m.id} (k={m.k})  "
        for block in gantt_data[m.id]:
            row += f"{block:<8} | "
        print(row)
    print("----------------------------------------------------------------------------\n")

def export_gantt_to_csv(makespan, mechanics, gantt_data, filename="schedule_output.csv"):
    """Exports the Gantt chart data directly into a CSV file for Excel visualization."""
    try:
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            
            # 1. Create and write the header row: [Mechanic Info, T=0, T=1, T=2, ...]
            header = ["Mechanic (k-limit)"] + [f"T={t}" for t in range(makespan)]
            writer.writerow(header)
            
            # 2. Write each mechanic's schedule as a row
            for m in mechanics:
                # Clean up the brackets and extra spaces for the Excel export
                clean_tasks = [task.strip("[] ") for task in gantt_data[m.id]]
                row = [f"M{m.id} (k={m.k})"] + clean_tasks
                writer.writerow(row)
                
 
    except IOError as e:
        print(f"[ERROR] Failed to write CSV file: {e}")

def main():
    output_log_file = "schedule_output.txt"
    sys.stdout = DualLogger(output_log_file)

    # Set seed for reproducible probabilistic events during presentation
    random.seed(42) 
    
    input_file = "garage_input.txt"
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        
    mechanics, templates, queue = parse_input(input_file)
    cars = build_garage_state(templates, queue)

    print_phase1_state(cars)
    
    # Run the simulation and capture output
    makespan, gantt_data = simulate(mechanics, cars)
    print_gantt_chart(makespan, mechanics, gantt_data)
    export_gantt_to_csv(makespan, mechanics, gantt_data)

if __name__ == "__main__":
    main()