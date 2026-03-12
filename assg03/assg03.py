import sys
import heapq
from math import ceil
from collections import defaultdict
from itertools import combinations



def parse_input(filename):
    assignments = {}
    deps = defaultdict(list)

    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            parts = line.split()
            
            if parts[0] in ['N', 'K']:
                continue
                
            if parts[0] == 'A':
                aid = int(parts[1])
                cost = int(parts[2])
                dep_list = []
                for d in parts[3:]:
                    if d == '0':
                        break
                    dep_list.append(int(d))
                assignments[aid] = cost
                deps[aid] = dep_list

    return assignments, deps




def is_gpt(a):

    return a % 2 == 0


def deps_done(a, completed, deps):

    return all(d in completed for d in deps[a])


def get_available_assignments(assignments, completed, shared, deps, gpt_limit, gem_limit):
    
    available = []
    for a in assignments:
        if a in completed:
            continue
        if not deps_done(a, shared, deps):
            continue
        if is_gpt(a):
            if assignments[a] > gpt_limit:
                continue
        else:
            if assignments[a] > gem_limit:
                continue
        available.append(a)
    return available


def is_valid_combo_caseA(combo, assignments, gpt_limit, gem_limit):
    gpt_used = sum(assignments[a] for a in combo if is_gpt(a))
    gem_used = sum(assignments[a] for a in combo if not is_gpt(a))
    return gpt_used <= gpt_limit and gem_used <= gem_limit



def heuristic(completed, assignments, deps, gpt_limit, gem_limit, num_students, case_type):

    remaining = [a for a in assignments if a not in completed]
    if not remaining:
        return 0


    memo = {}
    def depth(a):
        if a in memo:
            return memo[a]
        if a in completed:
            memo[a] = 0
        elif not deps[a] or all(d in completed for d in deps[a]):
            memo[a] = 1
        else:
            memo[a] = 1 + max(depth(d) for d in deps[a] if d not in completed)
        return memo[a]
    
    dep_bound = max(depth(a) for a in remaining) if remaining else 0

    if case_type == "A":
        simple_bound = ceil(len(remaining) / num_students)
        
        rem_gpt = sum(assignments[a] for a in remaining if is_gpt(a))
        rem_gem = sum(assignments[a] for a in remaining if not is_gpt(a))
        
        prompt_bound = 0
        if gpt_limit > 0 and rem_gpt > 0:
            prompt_bound = max(prompt_bound, ceil(rem_gpt / gpt_limit))
        if gem_limit > 0 and rem_gem > 0:
            prompt_bound = max(prompt_bound, ceil(rem_gem / gem_limit))
        
        return max(simple_bound, prompt_bound, dep_bound)
    
    else:
        rem_gpt = sum(assignments[a] for a in remaining if is_gpt(a))
        rem_gem = sum(assignments[a] for a in remaining if not is_gpt(a))

        prompt_bound = 0
        if gpt_limit > 0 and rem_gpt > 0:
            prompt_bound = max(prompt_bound, ceil(rem_gpt / gpt_limit))
        elif gpt_limit == 0 and rem_gpt > 0:
            return float('inf')
        
        if gem_limit > 0 and rem_gem > 0:
            prompt_bound = max(prompt_bound, ceil(rem_gem / gem_limit))
        elif gem_limit == 0 and rem_gem > 0:
            return float('inf')

        return max(prompt_bound, dep_bound)



def solve_caseA(algo, assignments, deps, gpt_limit, gem_limit, num_students, deadline=None):
    nodes = 0
    best = float('inf')
    best_path = None

    if algo == "DFS":
        def dfs(completed, day, shared, path):
            nonlocal nodes, best, best_path
            nodes += 1

            if deadline and day > deadline:
                return

            if completed == set(assignments.keys()):
                if day < best:
                    best = day
                    best_path = path.copy()
                return

            available = get_available_assignments(assignments, completed, shared, 
                                                 deps, gpt_limit, gem_limit)
            
            if not available:
                dfs(completed, day + 1, set(completed), path)
                return
            
            max_today = min(num_students, len(available))
            for count in range(1, max_today + 1):
                for combo in combinations(available, count):
                    if not is_valid_combo_caseA(combo, assignments, gpt_limit, gem_limit):
                        continue
                    new_completed = completed | set(combo)
                    new_path = path + [(day, list(combo))]
                    dfs(new_completed, day + 1, new_completed, new_path)

        dfs(set(), 1, set(), [])

    elif algo == "DFBB":
        def dfbb(completed, day, shared, path):
            nonlocal nodes, best, best_path
            nodes += 1

            if deadline and day > deadline:
                return

            if completed == set(assignments.keys()):
                if day < best:
                    best = day
                    best_path = path.copy()
                return

            if day >= best:
                return

            available = get_available_assignments(assignments, completed, shared,
                                                 deps, gpt_limit, gem_limit)
            
            if not available:
                dfbb(completed, day + 1, set(completed), path)
                return
            
            max_today = min(num_students, len(available))
            for count in range(1, max_today + 1):
                for combo in combinations(available, count):
                    if not is_valid_combo_caseA(combo, assignments, gpt_limit, gem_limit):
                        continue
                    new_completed = completed | set(combo)
                    new_path = path + [(day, list(combo))]
                    dfbb(new_completed, day + 1, new_completed, new_path)

        dfbb(set(), 1, set(), [])

    else: 
        counter = 0
        open_list = []
        start_h = heuristic(frozenset(), assignments, deps, gpt_limit, gem_limit, 
                          num_students, "A")
        heapq.heappush(open_list, (1 + start_h, counter, frozenset(), 1, frozenset(), []))
        visited = {}

        while open_list:
            f, _, completed, day, shared, path = heapq.heappop(open_list)
            nodes += 1

            if completed == frozenset(assignments.keys()):
                return day - 1, path, nodes

            if deadline and day > deadline:
                continue

            state = (completed, day)
            if state in visited:
                continue
            visited[state] = True

            available = get_available_assignments(assignments, set(completed), 
                                                 set(shared), deps, gpt_limit, gem_limit)
            
            if not available:
                counter += 1
                new_shared = frozenset(completed)
                h = heuristic(completed, assignments, deps, gpt_limit, gem_limit,
                            num_students, "A")
                heapq.heappush(open_list, (day + 1 + h, counter, completed, 
                                          day + 1, new_shared, path))
                continue
            
            max_today = min(num_students, len(available))
            for count in range(1, max_today + 1):
                for combo in combinations(available, count):
                    if not is_valid_combo_caseA(combo, assignments, gpt_limit, gem_limit):
                        continue
                    new_completed = frozenset(set(completed) | set(combo))
                    new_shared = frozenset(new_completed)
                    new_path = path + [(day, list(combo))]
                    
                    h = heuristic(new_completed, assignments, deps, gpt_limit, gem_limit,
                                num_students, "A")
                    
                    counter += 1
                    heapq.heappush(open_list, (day + 1 + h, counter, new_completed,
                                              day + 1, new_shared, new_path))

    if best == float('inf'):
        return None, None, nodes
    return best, best_path, nodes


def solve_caseB(algo, assignments, deps, gpt_limit, gem_limit, num_students, deadline=None): 

    nodes = 0
    best = float('inf')
    best_path = None

    if algo == "DFS":
        def dfs(completed, day, gpt_left, gem_left, shared, path):
            nonlocal nodes, best, best_path
            nodes += 1

            if deadline and day > deadline:
                return

            if completed == set(assignments.keys()):
                if day < best:
                    best = day
                    best_path = path.copy()
                return

            progress = False

            for a in assignments:
                if a in completed:
                    continue
                if not deps_done(a, shared, deps):
                    continue

                if is_gpt(a):
                    if gpt_left < assignments[a]:
                        continue
                    next_gpt = gpt_left - assignments[a]
                    next_gem = gem_left
                else:
                    if gem_left < assignments[a]:
                        continue
                    next_gem = gem_left - assignments[a]
                    next_gpt = gpt_left

                progress = True
                completed.add(a)
                dfs(completed, day, next_gpt, next_gem, shared, path + [(day, a)])
                completed.remove(a)

            if not progress:
                dfs(completed, day + 1, gpt_limit, gem_limit, set(completed), path)

        dfs(set(), 1, gpt_limit, gem_limit, set(), [])

    elif algo == "DFBB":
        def dfbb(completed, day, gpt_left, gem_left, shared, path):
            nonlocal nodes, best, best_path
            nodes += 1

            if deadline and day > deadline:
                return

            if completed == set(assignments.keys()):
                if day < best:
                    best = day
                    best_path = path.copy()
                return

            if day >= best:
                return

            progress = False

            for a in assignments:
                if a in completed:
                    continue
                if not deps_done(a, shared, deps):
                    continue

                if is_gpt(a):
                    if gpt_left < assignments[a]:
                        continue
                    next_gpt = gpt_left - assignments[a]
                    next_gem = gem_left
                else:
                    if gem_left < assignments[a]:
                        continue
                    next_gem = gem_left - assignments[a]
                    next_gpt = gpt_left

                progress = True
                completed.add(a)
                dfbb(completed, day, next_gpt, next_gem, shared, path + [(day, a)])
                completed.remove(a)

            if not progress:
                dfbb(completed, day + 1, gpt_limit, gem_limit, set(completed), path)

        dfbb(set(), 1, gpt_limit, gem_limit, set(), [])

    else: 
        counter = 0
        open_list = []
        start_h = heuristic(frozenset(), assignments, deps, 
                          gpt_limit, gem_limit, num_students, "B")
        start_state = (frozenset(), 1, gpt_limit, gem_limit, frozenset(), [])
        heapq.heappush(open_list, (1 + start_h, counter, start_state))
        visited = {}

        while open_list:
            f, _, state = heapq.heappop(open_list)
            completed, day, gpt_left, gem_left, shared, path = state
            nodes += 1

            if completed == frozenset(assignments.keys()):
                return day, path, nodes

            if deadline and day > deadline:
                continue

            state_id = (completed, day, gpt_left, gem_left, shared)
            if state_id in visited:
                continue
            visited[state_id] = True

            progress = False

            for a in assignments:
                if a in completed:
                    continue
                if not deps_done(a, shared, deps):
                    continue

                if is_gpt(a):
                    if gpt_left < assignments[a]:
                        continue
                    next_gpt = gpt_left - assignments[a]
                    next_gem = gem_left
                else:
                    if gem_left < assignments[a]:
                        continue
                    next_gem = gem_left - assignments[a]
                    next_gpt = gpt_left

                progress = True
                new_completed = frozenset(set(completed) | {a})
                new_path = path + [(day, a)]

                h = heuristic(new_completed, assignments, deps,
                            gpt_limit, gem_limit, num_students, "B")

                counter += 1
                new_state = (new_completed, day, next_gpt, next_gem, shared, new_path)
                heapq.heappush(open_list, (day + h, counter, new_state))

            if not progress:
                counter += 1
                new_state = (completed, day + 1, gpt_limit, gem_limit,
                           frozenset(completed), path)
                h = heuristic(completed, assignments, deps, 
                            gpt_limit, gem_limit, num_students, "B")
                heapq.heappush(open_list, (day + 1 + h, counter, new_state))

    if best == float('inf'):
        return None, None, nodes
    return best, best_path, nodes



def query1(case_type, assignments, deps, gpt_limit, gem_limit, num_students):

    print(f"QUERY 1: Case {case_type}")
    print(f"Group Size: {num_students} students")
    print(f"Subscription: ChatGPT={gpt_limit}, Gemini={gem_limit} prompts/day")

    for algo in ["DFS", "DFBB", "ASTAR"]:
        print(f"Algorithm: {algo}")

        if case_type == "A":
            days, seq, nodes = solve_caseA(algo, assignments, deps, gpt_limit, gem_limit, num_students)
        else:
            days, seq, nodes = solve_caseB(algo, assignments, deps, gpt_limit, gem_limit, num_students)

        if days is None:
            print("Result: NO SOLUTION")
        else:
            print(f"Minimum Days: {days}")
            print(f"Nodes Expanded: {nodes}")
            if seq:
                print("Schedule:")
                for day_num, day_assignments in seq:
                    if isinstance(day_assignments, list):
                    
                        gpt_used = sum(assignments[a] for a in day_assignments if is_gpt(a))
                        gem_used = sum(assignments[a] for a in day_assignments if not is_gpt(a))
                        print(f"  Day {day_num}:", end="")
                        for a in day_assignments:
                            llm = "ChatGPT" if is_gpt(a) else "Gemini"
                            print(f" A{a}({llm},{assignments[a]})", end="")
                        print(f"  [GPT:{gpt_used}/{gpt_limit}, Gem:{gem_used}/{gem_limit}]")
                    else:
                    
                        a = day_assignments
                        llm = "ChatGPT" if is_gpt(a) else "Gemini"
                        print(f"  Day {day_num}: A{a} ({llm}, {assignments[a]} prompts)")
        print()



def query2(case_type, assignments, deps, deadline, c1, c2, num_students):
    print(f"QUERY 2: Case {case_type}")
    print(f"Group Size: {num_students} students")
    print(f"Deadline: {deadline} days")
    print(f"Costs: ChatGPT={c1}, Gemini={c2} per prompt")

    total_gpt = sum(assignments[a] for a in assignments if is_gpt(a))
    total_gem = sum(assignments[a] for a in assignments if not is_gpt(a))
    



    best_cost = float('inf')
    best_scheme = None
    best_seq = None
    
    min_gpt = max((assignments[a] for a in assignments if is_gpt(a)), default=1)
    min_gem = max((assignments[a] for a in assignments if not is_gpt(a)), default=1)
    max_gpt = total_gpt
    max_gem = total_gem

    for gpt in range(min_gpt, max_gpt + 1):
        for gem in range(min_gem, max_gem + 1):
            cost = gpt * c1 + gem * c2
            
            if cost >= best_cost:
                continue

            if case_type == "A":
                days, seq, _ = solve_caseA("ASTAR", assignments, deps, 
                                          gpt, gem, num_students, deadline)
            else:
                days, seq, _ = solve_caseB("ASTAR", assignments, deps, 
                                          gpt, gem, num_students, deadline)

            if days is not None and days <= deadline:
                print(f"  Found: GPT={gpt}, Gemini={gem}, Cost={cost}, Days={days}")
                if cost < best_cost:
                    best_cost = cost
                    best_scheme = (gpt, gem)
                    best_seq = seq

    if best_scheme is None:
        print("Result: IMPOSSIBLE")
    else:
        print(f"Optimal: ChatGPT={best_scheme[0]}, Gemini={best_scheme[1]}")
        print(f"Cost: {best_cost}")
        print("\nSchedule:")
        for day_num, day_assignments in best_seq:
            if isinstance(day_assignments, list):
                gpt_used = sum(assignments[a] for a in day_assignments if is_gpt(a))
                gem_used = sum(assignments[a] for a in day_assignments if not is_gpt(a))
                print(f"  Day {day_num}:", end="")
                for a in day_assignments:
                    llm = "ChatGPT" if is_gpt(a) else "Gemini"
                    print(f" A{a}({llm},{assignments[a]})", end="")
                print(f"  [GPT:{gpt_used}, Gem:{gem_used}]")
            else:
                a = day_assignments
                llm = "ChatGPT" if is_gpt(a) else "Gemini"
                print(f"  Day {day_num}: A{a} ({llm}, {assignments[a]})")





def main():
    if len(sys.argv) < 5:
        print("Usage:")
        print("  Query 1: python3 assg03.py <file> <case> <N> 1 <gpt> <gem>")
        print("  Query 2: python3 assg03.py <file> <case> <N> 2 <deadline> <c1> <c2>")
        print("\nExample:")
        print("  python3 assg03.py input.txt A 3 1 5 5")
        print("  python3 assg03.py input.txt B 2 2 8 2 3")
        sys.exit(1)

    filename = sys.argv[1]
    case_type = sys.argv[2].upper()
    num_students = int(sys.argv[3])
    query = sys.argv[4]

    if case_type not in ["A", "B"]:
        print("Error: Case must be 'A' or 'B'")
        sys.exit(1)

    assignments, deps = parse_input(filename)
    print(f"\nLoaded {len(assignments)} assignments")

    if query == "1":
        if len(sys.argv) != 7:
            print("Error: Query 1 needs <gpt> <gem>")
            sys.exit(1)
        gpt = int(sys.argv[5])
        gem = int(sys.argv[6])
        query1(case_type, assignments, deps, gpt, gem, num_students)

    elif query == "2":
        if len(sys.argv) != 8:
            print("Error: Query 2 needs <deadline> <c1> <c2>")
            sys.exit(1)
        deadline = int(sys.argv[5])
        c1 = int(sys.argv[6])
        c2 = int(sys.argv[7])
        query2(case_type, assignments, deps, deadline, c1, c2, num_students)

    else:
        print("Error: Query must be '1' or '2'")
        sys.exit(1)


if __name__ == "__main__":
    main()