Prerequisites:
    -Python 3.x installed.
    -No external libraries are required (uses standard built-in modules only).

How to Run:

    -Step 1: Generate Test Data
        -First, generate the randomized input files (DAGs, mechanics, and daily queues).
        -Run the following command in terminal, replacing `<n>` with the number of test files needed.
            -command: python3 input_generator.py <n>

    -Step 2: Run the Simulation Engine
        -Execute the main scheduling algorithm by passing one of the generated text files as an argument by running the following command:
            -python3 main.py <filename.txt>

Expected Output:
    -Upon running main.py, the program will:
        -Print the Phase 1 Baseline State (In-degrees and T=0 tasks).
        -Print the Phase 2 Dynamic Simulation Log.
        -Print the final ASCII Gantt Chart showing the optimized makespan.
        -Save the console output to schedule_output.txt.
        -Export the final Gantt chart to schedule_output.csv for spreadsheet visualization.

Presentation:
 - https://cciitpatna-my.sharepoint.com/:p:/g/personal/virat_2511ai17_iitp_ac_in/IQAh9ve8gzmhRIpJXTqhQdwtAY8vbY1g7K5F5ZEu8kFr4kw?e=8C9pVS 