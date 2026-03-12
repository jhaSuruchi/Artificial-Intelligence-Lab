import sys
from z3 import *


def solve_charging_schedule(num_ports, port_prices, vehicle_requests):
    num_vehicles = len(vehicle_requests)
    assigned_port = [Int(f"assigned_port_{i}") for i in range(num_vehicles)]
    charge_start_time = [Int(f"charge_start_time_{i}") for i in range(num_vehicles)]
    optimizer = Optimize()

    for vehicle_index, (vehicle_id, arrival_time, departure_time, base_charge_time) in enumerate(vehicle_requests):
        optimizer.add(assigned_port[vehicle_index] >= 1)
        optimizer.add(assigned_port[vehicle_index] <= num_ports)
        for port in range(1, num_ports + 1):
            charge_duration = (base_charge_time + port - 1) // port
            optimizer.add(Implies(
                assigned_port[vehicle_index] == port,
                And(
                    charge_start_time[vehicle_index] >= arrival_time,
                    charge_start_time[vehicle_index] + charge_duration <= departure_time
                )
            ))

    for i in range(num_vehicles):
        for j in range(i + 1, num_vehicles):
            base_charge_time_i = vehicle_requests[i][3]
            base_charge_time_j = vehicle_requests[j][3]
            for port in range(1, num_ports + 1):
                charge_duration_i = (base_charge_time_i + port - 1) // port
                charge_duration_j = (base_charge_time_j + port - 1) // port
                optimizer.add(Implies(
                    And(assigned_port[i] == port, assigned_port[j] == port),
                    Or(
                        charge_start_time[i] + charge_duration_i <= charge_start_time[j],
                        charge_start_time[j] + charge_duration_j <= charge_start_time[i]
                    )
                ))

    vehicle_cost_expressions = []
    for vehicle_index, (vehicle_id, arrival_time, departure_time, base_charge_time) in enumerate(vehicle_requests):
        cost_expression = None
        for port in range(1, num_ports + 1):
            charge_duration = (base_charge_time + port - 1) // port
            cost_at_port = port_prices[port - 1] * charge_duration
            if cost_expression is None:
                cost_expression = If(assigned_port[vehicle_index] == port, cost_at_port, 0)
            else:
                cost_expression = If(assigned_port[vehicle_index] == port, cost_at_port, cost_expression)
        vehicle_cost_expressions.append(cost_expression)

    total_cost = Sum(vehicle_cost_expressions)
    optimizer.minimize(total_cost)

    if optimizer.check() == sat:
        solution_model = optimizer.model()
        print("\n\nSAT")
        print(f"\n{'Vehicle':>8} {'Port':>5} {'Duration':>9} {'Start':>6} {'End':>6} {'Cost':>7}")
        running_total_cost = 0
        for vehicle_index, (vehicle_id, arrival_time, departure_time, base_charge_time) in enumerate(vehicle_requests):
            optimal_port = solution_model[assigned_port[vehicle_index]].as_long()
            optimal_start = solution_model[charge_start_time[vehicle_index]].as_long()
            charge_duration = (base_charge_time + optimal_port - 1) // optimal_port
            vehicle_cost = port_prices[optimal_port - 1] * charge_duration
            running_total_cost += vehicle_cost
            print(f"{vehicle_id:>8} {optimal_port:>5} {charge_duration:>9} {optimal_start:>6} {optimal_start + charge_duration:>6} {vehicle_cost:>7}")
        print(f"\n\n{'TOTAL COST':>40} {running_total_cost:>7}\n\n")
    else:
        print("\n\nUNSAT\n\n")


def parse_input_file(file_path):
    num_ports = None
    port_prices = []
    vehicle_requests = []
    with open(file_path) as input_file:
        for raw_line in input_file:
            tokens = raw_line.strip().split()
            if not tokens:
                continue
            if tokens[0] == 'K':
                num_ports = int(tokens[1])
            elif tokens[0] == 'P':
                port_prices = [int(token) for token in tokens[1:]]
            elif tokens[0] == 'V':
                vehicle_requests.append((int(tokens[1]), int(tokens[2]), int(tokens[3]), int(tokens[4])))
    return num_ports, port_prices, vehicle_requests


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python assg04.py <input_file>")
        sys.exit(1)
    num_ports, port_prices, vehicle_requests = parse_input_file(sys.argv[1])
    solve_charging_schedule(num_ports, port_prices, vehicle_requests)