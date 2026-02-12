import sys
from collections import deque
from copy import deepcopy

def parse_input(filename):
    assig = {}
    dependencies = {}

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue

            part = line.split()
            if part[0] == 'A':
                aid = f"A{part[1]}"
                cost = int(part[2])
                deps = []
                for d in part[3:]:
                    if d == '0':
                        break
                    deps.append(f"A{d}")
                assig[aid] = cost
                dependencies[aid] = deps

    return assig, dependencies


def deps_satisfied_local(a, local_knowledge, dependencies):
    return all(dep in local_knowledge for dep in dependencies[a])


def earliest_completion(assg, dependencies, N, K):
    initial = (frozenset(), 1, tuple([0]*N))
    queue = deque([initial])
    visited = set()

    while queue:
        completed, day, prompts = queue.popleft()

        if completed == frozenset(assg.keys()):
            return day

        if (completed, day, prompts) in visited:
            continue
        visited.add((completed, day, prompts))

        progress = False

        for a in assg:
            if a in completed:
                continue
            if not all(dep in completed for dep in dependencies[a]):
                continue

            for s in range(N):
                if prompts[s] + assg[a] <= K:
                    progress = True
                    new_completed = set(completed)
                    new_completed.add(a)

                    new_prompts = list(prompts)
                    new_prompts[s] += assg[a]

                    queue.append((
                        frozenset(new_completed),
                        day,
                        tuple(new_prompts)
                    ))

        if not progress:
            queue.append((completed, day + 1, tuple([0]*N)))

    return None



def can_finish(assig, dependencies, N, K, maxDays):

    def dfs(completed, day, prompts):
        if completed == set(assig.keys()):
            return True
        if day > maxDays:
            return False

        progress = False

        for a in assig:
            if a in completed:
                continue
            if not all(dep in completed for dep in dependencies[a]):
                continue

            for s in range(N):
                if prompts[s] + assig[a] <= K:
                    progress = True
                    completed.add(a)
                    prompts[s] += assig[a]

                    if dfs(completed, day, prompts):
                        return True

                    prompts[s] -= assig[a]
                    completed.remove(a)

        if not progress:
            return dfs(completed, day + 1, [0]*N)

        return False

    return dfs(set(), 1, [0]*N)



def minimum_K(assignments, dependencies, N, max_days):
    K = 1
    while True:
        if can_finish(assignments, dependencies, N, K, max_days):
            return K
        K += 1



def earliest_completion_delayed(assig, dependencies, N, K):
    init_knowledge = tuple(frozenset() for _ in range(N))
    initial = (frozenset(), 1, tuple([0]*N), init_knowledge)

    queue = deque([initial])
    visited = set()

    while queue:
        completed, day, prompts, knowledge = queue.popleft()

        if completed == frozenset(assig.keys()):
            return day

        state_id = (completed, day, prompts, knowledge)
        if state_id in visited:
            continue
        visited.add(state_id)

        progress = False

        for a in assig:
            if a in completed:
                continue

            for s in range(N):
                if not deps_satisfied_local(a, knowledge[s], dependencies):
                    continue
                if prompts[s] + assig[a] <= K:
                    progress = True

                    new_completed = set(completed)
                    new_completed.add(a)

                    new_prompts = list(prompts)
                    new_prompts[s] += assig[a]

                    new_knowledge = [set(k) for k in knowledge]
                    new_knowledge[s].add(a)

                    queue.append((
                        frozenset(new_completed),
                        day,
                        tuple(new_prompts),
                        tuple(frozenset(k) for k in new_knowledge)
                    ))

        if not progress:
            shared = set(completed)
            new_knowledge = tuple(frozenset(shared) for _ in range(N))
            queue.append((
                completed,
                day + 1,
                tuple([0]*N),
                new_knowledge
            ))

    return None





def can_finish_delayed(assigs, dependencies, N, K, max_days):

    def dfs(completed, day, prompts, knowledge):
        if completed == set(assigs.keys()):
            return True
        if day > max_days:
            return False

        progress = False

        for a in assigs:
            if a in completed:
                continue

            for s in range(N):
                if not deps_satisfied_local(a, knowledge[s], dependencies):
                    continue
                if prompts[s] + assigs[a] <= K:
                    progress = True

                    completed.add(a)
                    prompts[s] += assigs[a]
                    knowledge[s].add(a)

                    if dfs(completed, day, prompts, knowledge):
                        return True

                    knowledge[s].remove(a)
                    prompts[s] -= assigs[a]
                    completed.remove(a)

        if not progress:
            shared = set(completed)
            new_knowledge = [shared.copy() for _ in range(N)]
            return dfs(completed, day + 1, [0]*N, new_knowledge)

        return False

    return dfs(set(), 1, [0]*N, [set() for _ in range(N)])





def minimum_K_delayed(assigs, dependencies, N, maxDays):
    K = 1
    while True:
        if can_finish_delayed(assigs, dependencies, N, K, maxDays):
            return K
        K += 1

def main():
    if len(sys.argv) < 4:
        print("Usage:")
        print("python assg02.py <input-file> <mode> <params>")
        print("Modes:")
        print("  part1 <N> <K>")
        print("  part2 <N> <days>")
        print("  part3a <N> <K>")
        print("  part3b <N> <days>")
        return

    filename = sys.argv[1]
    mode = sys.argv[2]

    assigs, dependencies = parse_input(filename)
    max_cost = 0
    for a in assigs:
        if assigs[a] > max_cost:
            max_cost = assigs[a]
    

    if mode == "part1":
        N, K = int(sys.argv[3]), int(sys.argv[4])

        if K < max_cost:
            print("Earliest completion day: Infinity")
            return
        print("Earliest completion day:", earliest_completion(assigs, dependencies, N, K))

    elif mode == "part2":
        N, days = int(sys.argv[3]), int(sys.argv[4])
        print("Minimum prompts per student per day:", minimum_K(assigs, dependencies, N, days))

    elif mode == "part3a":
        N, K = int(sys.argv[3]), int(sys.argv[4])
        if K < max_cost:
            print("Earliest completion day (delayed sharing): Infinity")
            return
        res = earliest_completion_delayed(assigs, dependencies, N, K)
        print("Earliest completion day (delayed sharing):", res)

    elif mode == "part3b":
        N, days = int(sys.argv[3]), int(sys.argv[4])
        res = minimum_K_delayed(assigs, dependencies, N, days)
        if res is None:
            print("Result: IMPOSSIBLE within given days")
        else:
            print("Minimum prompts per student per day (delayed sharing):", res)

    else:
        print("Invalid mode")


if __name__ == "__main__":
    main()
