import random
import os


def generate_testcase(seed, output_dir, index):
    random.seed(seed)

    num_ports = random.randint(2, 6)

    base_price = random.randint(3, 8)
    port_prices = sorted([base_price + random.randint(k * 3, k * 5 + 5) for k in range(num_ports)])

    num_vehicles = random.randint(15, 30)
    max_time = num_vehicles * random.randint(8, 12)

    vehicle_requests = []
    for vehicle_id in range(1, num_vehicles + 1):
        for _ in range(500):
            arrival_time = random.randint(0, max_time - 6)
            departure_time = min(arrival_time + random.randint(4, 25), max_time)
            base_charge_time = random.randint(1, departure_time - arrival_time - 1) if departure_time - arrival_time > 1 else 1
            if arrival_time + base_charge_time <= departure_time:
                vehicle_requests.append((vehicle_id, arrival_time, departure_time, base_charge_time))
                break

    lines = []
    lines.append(f"K {num_ports}")
    lines.append(f"P {' '.join(map(str, port_prices))}")
    for vehicle_id, arrival_time, departure_time, base_charge_time in vehicle_requests:
        lines.append(f"V {vehicle_id} {arrival_time} {departure_time} {base_charge_time}")

    filename = os.path.join(output_dir, f"input{str(index).zfill(2)}.txt")
    with open(filename, "w") as output_file:
        output_file.write("\n".join(lines) + "\n")


def main():
    output_dir = "testcases"
    os.makedirs(output_dir, exist_ok=True)

    for index in range(1, 101):
        generate_testcase(seed=index * 37, output_dir=output_dir, index=index)

    print(f"Generated 100 test cases in '{output_dir}/'")


main()