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