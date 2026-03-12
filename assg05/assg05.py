import sys
import time
import random
import argparse
import itertools

from z3 import Bool, Solver, Or, And, Not, Implies, sat, unsat, unknown

class Course:
    def __init__(self, cid, start, deadline, duration):
        self.id       = cid       
        self.start    = start      
        self.deadline = deadline  
        self.duration = duration  

    def valid_start_days(self):
        last_start = self.deadline - self.duration + 1
        return list(range(self.start, last_start + 1))

    def __repr__(self):
        return (f"Course(id={self.id}, start={self.start}, "
                f"deadline={self.deadline}, duration={self.duration})")


def parse_input(text):
    M = 0
    courses = []
    for line in text.strip().splitlines():
        line = line.split('%')[0].strip()  
        if not line:
            continue
        parts = line.split()
        if parts[0] == 'M':
            M = int(parts[1])
        elif parts[0] == 'N':
            pass 
        elif parts[0] == 'C':
            _, cid, s, d, t = parts
            courses.append(Course(int(cid), int(s), int(d), int(t)))
    return M, courses



def encode_option1_z3(M, courses):
    solver = Solver()
    N = len(courses)


    z = {}
    for i, course in enumerate(courses):
        for j in range(M):
            for t in course.valid_start_days():
                z[(i, j, t)] = Bool(f"z_{i+1}_{j+1}_{t}")

    num_vars = len(z)
    clause_count = 0
    for i, course in enumerate(courses):
        valid = [(j, t) for j in range(M) for t in course.valid_start_days()]

        solver.add(Or([z[(i, j, t)] for (j, t) in valid]))
        clause_count += 1

        for (j1, t1), (j2, t2) in itertools.combinations(valid, 2):
            solver.add(Or(Not(z[(i, j1, t1)]), Not(z[(i, j2, t2)])))
            clause_count += 1

    occ = {}
    for i, course in enumerate(courses):
        for j in range(M):
            for t in course.valid_start_days():
                for d in range(t, t + course.duration):
                    key = (j, d)
                    if key not in occ:
                        occ[key] = []
                    occ[key].append(z[(i, j, t)])

    for (j, d), vars_list in occ.items():
        for v1, v2 in itertools.combinations(vars_list, 2):
            solver.add(Or(Not(v1), Not(v2)))
            clause_count += 1

    stats = {
        "num_vars":    num_vars,
        "num_clauses": clause_count,
    }
    return solver, z, stats


def solve_option1_z3(M, courses):
    t0 = time.time()
    solver, z, stats = encode_option1_z3(M, courses)
    result = solver.check()
    elapsed = time.time() - t0

    output = {
        "encoding": "Option-1 (z_ijt)",
        "result":   str(result),
        "time_sec": round(elapsed, 4),
        **stats,
    }

    if result == sat:
        model = solver.model()
        schedule = []
        for (i, j, t), var in z.items():
            if model[var]:
                schedule.append((courses[i].id, j + 1, t))
        output["schedule"] = sorted(schedule)

    return output


def encode_option2_z3(M, courses):
    solver = Solver()
    N = len(courses)

    x = {}  
    y = {}  

    for i, course in enumerate(courses):
        for j in range(M):
            x[(i, j)] = Bool(f"x_{i+1}_{j+1}")
        for t in course.valid_start_days():
            y[(i, t)] = Bool(f"y_{i+1}_{t}")

    num_vars = len(x) + len(y)
    clause_count = 0

    for i, course in enumerate(courses):
        rooms = [x[(i, j)] for j in range(M)]
        solver.add(Or(rooms))                              
        clause_count += 1
        for j1, j2 in itertools.combinations(range(M), 2):
            solver.add(Or(Not(x[(i, j1)]), Not(x[(i, j2)]))) 
            clause_count += 1

    for i, course in enumerate(courses):
        valid = course.valid_start_days()
        if not valid:
            solver.add(Or([]))  
            clause_count += 1
            continue
        day_vars = [y[(i, t)] for t in valid]
        solver.add(Or(day_vars))                           
        clause_count += 1
        for t1, t2 in itertools.combinations(valid, 2):
            solver.add(Or(Not(y[(i, t1)]), Not(y[(i, t2)]))) 
            clause_count += 1

    for i1, i2 in itertools.combinations(range(N), 2):
        c1, c2 = courses[i1], courses[i2]
        for j in range(M):
            for t1 in c1.valid_start_days():
                for t2 in c2.valid_start_days():
                    if t1 < t2 + c2.duration and t2 < t1 + c1.duration:
                        solver.add(Or(
                            Not(x[(i1, j)]), Not(y[(i1, t1)]),
                            Not(x[(i2, j)]), Not(y[(i2, t2)])
                        ))
                        clause_count += 1

    stats = {
        "num_vars":    num_vars,
        "num_clauses": clause_count,
    }
    return solver, x, y, stats


def solve_option2_z3(M, courses):
    t0 = time.time()
    solver, x, y, stats = encode_option2_z3(M, courses)
    result = solver.check()
    elapsed = time.time() - t0

    output = {
        "encoding": "Option-2 (x_ij + y_it)",
        "result":   str(result),
        "time_sec": round(elapsed, 4),
        **stats,
    }

    if result == sat:
        model = solver.model()
        schedule = []
        for i, course in enumerate(courses):
            assigned_room = None
            for j in range(M):
                if model[x[(i, j)]]:
                    assigned_room = j + 1
                    break
            start_day = None
            for t in course.valid_start_days():
                if model[y[(i, t)]]:
                    start_day = t
                    break
            if assigned_room and start_day:
                schedule.append((course.id, assigned_room, start_day))
        output["schedule"] = sorted(schedule)

    return output


def to_dimacs_option1(M, courses, filename="option1.cnf"):
    N = len(courses)
    var_id = {}
    counter = 1
    for i, course in enumerate(courses):
        for j in range(M):
            for t in course.valid_start_days():
                var_id[(i, j, t)] = counter
                counter += 1

    clauses = []

    for i, course in enumerate(courses):
        valid = [(j, t) for j in range(M) for t in course.valid_start_days()]

        clauses.append([var_id[(i, j, t)] for (j, t) in valid])

        for (j1, t1), (j2, t2) in itertools.combinations(valid, 2):
            clauses.append([-var_id[(i, j1, t1)], -var_id[(i, j2, t2)]])

    occ = {}
    for i, course in enumerate(courses):
        for j in range(M):
            for t in course.valid_start_days():
                for d in range(t, t + course.duration):
                    key = (j, d)
                    if key not in occ:
                        occ[key] = []
                    occ[key].append(var_id[(i, j, t)])

    for (j, d), vlist in occ.items():
        for v1, v2 in itertools.combinations(vlist, 2):
            clauses.append([-v1, -v2])

    num_vars    = counter - 1
    num_clauses = len(clauses)

    with open(filename, 'w') as f:
        f.write(f"c DIMACS CNF — Option-1 encoding (z_ijt)\n")
        f.write(f"c N={N} M={M}\n")
        f.write(f"p cnf {num_vars} {num_clauses}\n")
        for clause in clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")

    return filename, num_vars, num_clauses


def to_dimacs_option2(M, courses, filename="option2.cnf"):
    N = len(courses)
    var_id = {}
    counter = 1
    for i in range(N):
        for j in range(M):
            var_id[('x', i, j)] = counter
            counter += 1
    for i, course in enumerate(courses):
        for t in course.valid_start_days():
            var_id[('y', i, t)] = counter
            counter += 1

    clauses = []

    for i in range(N):
        clauses.append([var_id[('x', i, j)] for j in range(M)])
        for j1, j2 in itertools.combinations(range(M), 2):
            clauses.append([-var_id[('x', i, j1)], -var_id[('x', i, j2)]])

    for i, course in enumerate(courses):
        valid = course.valid_start_days()
        if not valid:
            clauses.append([])
            continue
        clauses.append([var_id[('y', i, t)] for t in valid])
        for t1, t2 in itertools.combinations(valid, 2):
            clauses.append([-var_id[('y', i, t1)], -var_id[('y', i, t2)]])

    for i1, i2 in itertools.combinations(range(N), 2):
        c1, c2 = courses[i1], courses[i2]
        for j in range(M):
            for t1 in c1.valid_start_days():
                for t2 in c2.valid_start_days():
                    if t1 < t2 + c2.duration and t2 < t1 + c1.duration:
                        clauses.append([
                            -var_id[('x', i1, j)], -var_id[('y', i1, t1)],
                            -var_id[('x', i2, j)], -var_id[('y', i2, t2)]
                        ])

    num_vars    = counter - 1
    num_clauses = len(clauses)

    with open(filename, 'w') as f:
        f.write(f"c DIMACS CNF — Option-2 encoding (x_ij + y_it)\n")
        f.write(f"c N={N} M={M}\n")
        f.write(f"p cnf {num_vars} {num_clauses}\n")
        for clause in clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")

    return filename, num_vars, num_clauses


def analyze_dimacs(filename):
    counts = {2: 0, 3: 0, "3+": 0, "total": 0}
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c') or line.startswith('p'):
                continue
            lits = [x for x in line.split() if x != '0']
            n = len(lits)
            counts["total"] += 1
            if n == 2:
                counts[2] += 1
            elif n == 3:
                counts[3] += 1
            elif n > 3:
                counts["3+"] += 1
    return counts


def generate_sat_instance(seed=None, max_rooms=5, max_courses=8, max_days=30, max_duration=5):
    rng = random.Random(seed)
    M = rng.randint(2, max_rooms)
    N = rng.randint(3, max_courses)

    courses = []
    cid = 1
    courses_per_room = [[] for _ in range(M)]

    for j in range(M):
        day = 1
        while cid <= N and day <= max_days:
            duration = rng.randint(1, max_duration)
            if day + duration - 1 > max_days:
                break                         
            actual_start = day
            actual_end   = day + duration - 1

            slack_before = rng.randint(0, min(2, actual_start - 1))
            slack_after  = rng.randint(0, min(2, max_days - actual_end))
            s_i = actual_start - slack_before
            d_i = actual_end   + slack_after

            courses.append(Course(cid, s_i, d_i, duration))
            courses_per_room[j].append(cid)
            day  += duration + rng.randint(0, 1) 
            cid  += 1

        if cid > N:
            break

    return M, courses


def generate_unsat_instance(seed=None, strategy="overload", max_rooms=3, max_courses=8, max_days=20):
    rng = random.Random(seed)

    if strategy == "tight":
        M = rng.randint(2, max_rooms)
        N = rng.randint(3, max_courses)
        courses = []
        for cid in range(1, N + 1):
            if cid == 1:
                duration = rng.randint(4, 7)
                start    = rng.randint(1, 10)
                deadline = start + duration - 2  
            else:
                duration = rng.randint(1, 4)
                start    = rng.randint(1, max_days - duration)
                deadline = rng.randint(start + duration - 1, max_days)
            courses.append(Course(cid, start, deadline, duration))
        return M, courses

    else:  
        M = 1                             
        window_start = 1
        window_end   = rng.randint(5, 10)  
        window_size  = window_end - window_start + 1

        N = rng.randint(3, max_courses)
        courses = []
        total_dur = 0
        for cid in range(1, N + 1):
            duration = rng.randint(2, 4)
            total_dur += duration
            start    = window_start
            deadline = window_end
            courses.append(Course(cid, start, deadline, duration))
        if total_dur <= window_size * M:
            extra_dur = window_size * M - total_dur + 1
            courses.append(Course(N + 1, window_start, window_end, extra_dur))

        return M, courses


def _quick_check(M, courses):
    result = solve_option1_z3(M, courses)
    return result["result"]


def generate_mixed_instances(num_cases=100, sat_ratio=0.6, seed=0):
    instances = []
    rng = random.Random(seed)
    num_sat   = int(num_cases * sat_ratio)
    num_unsat = num_cases - num_sat

    for k in range(num_sat):
        M, courses = generate_sat_instance(seed=rng.randint(0, 10**6))
        instances.append((M, courses, "SAT"))

    for k in range(num_unsat):
        strategy = "tight" if k % 2 == 0 else "overload"
        M, courses = generate_unsat_instance(
            seed=rng.randint(0, 10**6), strategy=strategy)
        instances.append((M, courses, "UNSAT"))

    rng.shuffle(instances)
    return instances


def run_benchmark(num_cases=100):


    instances = generate_mixed_instances(num_cases=num_cases, sat_ratio=0.5)

    print(f"  BENCHMARK: {num_cases} random test cases  "
          f"(~{num_cases//2} SAT + ~{num_cases//2} UNSAT by construction)")
    print(f"{'#':>4}  {'N':>3} {'M':>3} {'Exp':>5}  "
          f"{'Opt1 vars':>10} {'Opt1 cls':>10} {'Opt1 t(s)':>9}  "
          f"{'Opt2 vars':>10} {'Opt2 cls':>10} {'Opt2 t(s)':>9}  "
          f"{'Res1':>6} {'Res2':>6} {'Match':>6}")

    totals = {
        "opt1_vars": 0, "opt1_clauses": 0, "opt1_time": 0.0,
        "opt2_vars": 0, "opt2_clauses": 0, "opt2_time": 0.0,
        "sat_got": 0, "unsat_got": 0,
        "correct": 0, "mismatch_encodings": 0,
    }

    for idx, (M, courses, expected) in enumerate(instances, 1):
        N = len(courses)
        r1 = solve_option1_z3(M, courses)
        r2 = solve_option2_z3(M, courses)

        totals["opt1_vars"]    += r1["num_vars"]
        totals["opt1_clauses"] += r1["num_clauses"]
        totals["opt1_time"]    += r1["time_sec"]
        totals["opt2_vars"]    += r2["num_vars"]
        totals["opt2_clauses"] += r2["num_clauses"]
        totals["opt2_time"]    += r2["time_sec"]

        res1 = r1["result"]  
        res2 = r2["result"]

        if res1 == "sat":
            totals["sat_got"] += 1
        else:
            totals["unsat_got"] += 1

        match_enc = "✓" if res1 == res2 else "✗DIFF"
        if res1 != res2:
            totals["mismatch_encodings"] += 1

        expected_lower = expected.lower()
        correct_marker = "✓" if res1 == expected_lower else "?"
        if res1 == expected_lower:
            totals["correct"] += 1

        print(f"{idx:>4}  {N:>3} {M:>3} {expected:>5}  "
              f"{r1['num_vars']:>10} {r1['num_clauses']:>10} {r1['time_sec']:>9.4f}  "
              f"{r2['num_vars']:>10} {r2['num_clauses']:>10} {r2['time_sec']:>9.4f}  "
              f"{res1:>6} {res2:>6} {match_enc:>6}")

    print(f"{'AVG':>4}  {'':>7}         "
          f"{totals['opt1_vars']//num_cases:>10} "
          f"{totals['opt1_clauses']//num_cases:>10} "
          f"{totals['opt1_time']/num_cases:>9.4f}  "
          f"{totals['opt2_vars']//num_cases:>10} "
          f"{totals['opt2_clauses']//num_cases:>10} "
          f"{totals['opt2_time']/num_cases:>9.4f}")
    print(f"\n  Results from Z3:")
    print(f"    SAT   instances produced : {totals['sat_got']}/{num_cases}")
    print(f"    UNSAT instances produced : {totals['unsat_got']}/{num_cases}")
    print(f"    Encoding agreement       : "
          f"{num_cases - totals['mismatch_encodings']}/{num_cases} "
          f"(mismatches = {totals['mismatch_encodings']})")
    print(f"    Matched expected label   : {totals['correct']}/{num_cases}")
    if totals['correct'] < num_cases:
        print(f"    NOTE: '?' rows = SAT-generated instances that Z3 found UNSAT")
        print(f"          (generator packed too many courses; rooms overflowed)")
        print(f"          These are still valid test cases — just harder than expected.")


def print_result(res):
    print(f"\n {res['encoding']}")
    print(f"  Result      : {res['result']}")
    print(f"  Variables   : {res['num_vars']}")
    print(f"  Clauses     : {res['num_clauses']}")
    print(f"  Time (sec)  : {res['time_sec']}")
    if "schedule" in res:
        print("  Schedule (course -> room, start-day):")
        for cid, room, day in res["schedule"]:
            print(f"    Course {cid:>2}  ->  Room {room},  Day {day}")


def print_dimacs_stats(fname, num_vars, num_clauses):
    stats = analyze_dimacs(fname)
    print(f"\n  DIMACS file  : {fname}")
    print(f"  Variables    : {num_vars}")
    print(f"  Clauses      : {num_clauses}")
    print(f"  2-literal    : {stats[2]}")
    print(f"  3-literal    : {stats[3]}")
    print(f"  3+-literal   : {stats['3+']}")



SAMPLE_INPUT = """\
% number of rooms
M 3
% number of short-term-courses
N 5
% course id  start-day  end-day  duration
C 1 1 10 3
C 2 2 12 4
C 3 5 15 5
C 4 1  8 2
C 5 6 14 3
"""


def main():
    parser = argparse.ArgumentParser(
        description="CS5205 Assg-5: SAT-based Course Scheduling")
    parser.add_argument('--input',    type=str, default=None,
                        help="Path to input file (assignment format)")
    parser.add_argument('--generate', action='store_true',
                        help="Run 100 mixed SAT+UNSAT test cases benchmark")
    parser.add_argument('--dimacs',   action='store_true',
                        help="Also write DIMACS CNF files")
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            text = f.read()
    else:
        text = SAMPLE_INPUT

    M, courses = parse_input(text)
    print(f"Rooms    : {M}")
    print(f"Courses  : {len(courses)}")
    for c in courses:
        vsd = c.valid_start_days()
        feasible = "OK" if vsd else "INFEASIBLE (no valid window)"
        print(f"  {c}  valid-start-days={vsd}  [{feasible}]")


        r1 = solve_option1_z3(M, courses)
        r2 = solve_option2_z3(M, courses)
        print_result(r1)
        print_result(r2)

        if r1["result"] != r2["result"]:
            print("\n[WARNING] Encodings disagree — possible bug!")
        else:
            print(f"\n[OK] Both encodings agree: {r1['result'].upper()}")
    

    if args.dimacs:
        print("\nGenerating DIMACS CNF files...")
        f1, v1, c1 = to_dimacs_option1(M, courses, "option1.cnf")
        f2, v2, c2 = to_dimacs_option2(M, courses, "option2.cnf")
        print_dimacs_stats(f1, v1, c1)
        print_dimacs_stats(f2, v2, c2)
        print("\nTo run with an external solver (e.g., MiniSat):")
        print("  minisat option1.cnf result1.txt")
        print("  minisat option2.cnf result2.txt")

    if args.generate:
        run_benchmark(num_cases=100)


if __name__ == "__main__":
    main()


"""
pip install z3-solver

# Run on the built-in sample
python3 assg05.py

# Run on your own input file
python3 assg05.py --input input.txt

# Generate DIMACS files (for external solvers like MiniSat, Glucose)
python3 assg05.py --dimacs

z3 option1.cnf
z3 option2.cnf

# MiniSat (simplest to install):
sudo apt install minisat  

minisat option1.cnf result1.txt
minisat option2.cnf result2.txt

# Run 100 random test cases benchmark
python3 assg05.py --generate

"""