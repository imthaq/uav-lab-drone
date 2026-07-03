## Week-1  Completed Work :
    1. Raspberry Pi Lite OS installation.
    2. Setting up the OS and Installing different tools required to build a connection between the Raspberry Pi and other Sensors such as python , pip3 , i2c , smbus2 and so on as required. 
    3. Creating a connection between Raspberry and VL53L0X sensor.
    4. Writing the code required to initialize the VL53L0X sensor and testing the sensor at different distance making sure it is working properly and saving the results in CSV format as well.
    5. Creating a connection between the TCA9548A and Raspberry Pi and then connecting different sensors to TCA9548A and operating all of them at once.
    6. Testing all the other VL53L0X sensors through the MUX(TCA9548A) making sure all are working fine or not.
    7. Starting the basic research work, collecting all the necessary research papers regarding the SystemC , RISC-V , UAV testing , Obstacle detection , Swarms formation and so on.
    8. Adding all the necessary details required from the research papers we found and categorizing them into 2 different sections, adding the details  into the Google sheet table properly formatted and made by Imtishal.
       
## Challenges faced during week-1: 
    1. First before we begin with OS installation we need to burn the Raspberry Pi iso image into a SD-card. However the iso image was not getting burned properly and causing issue during installation process. Reason ?  for this was the SD-card was not properly formatted I.e the space was not properly allocated to any section of the card  causing errors during read and write process. Solution? The solution to this issue was that we properly format the SD-card, then burn the ISO images and  install the OS,and thus after doing each step carefully we were successful in installing the OS.
       
    2. Second Problem we faced was the connection of MUX with the sensor. The MUX(TCA9548A) was not properly detecting the sensor we connected with it even tho the code written was correct. Reason ? The SDA wire  of sensor was connected with the SC0 part of the mux and SCA wire was connected with SD0 which was wrong it should be connected in opposite way. SCA→SC0 and SDA→SD0. Solution? After identifying this issue we properly connected the sensors and everything started working fine as usual. Thus all VL53L0X sensors were detected and working fine, similarly all the output port of the MUX(TCA9548A) were working fine and giving correct output.



## Week 3 Progress Report: 

- Worked on connecting the camera with the raspberry P1 4. At first the there was an error in the OS such that the file system was corrupted and there was no fix at all because the main issue lied  inside SD card itself . We had to redo everything from the start such as installing the python interpretor, other basic functionalities and required libraries to run the code. After doing all the basic stuff and comfirming everything needed was installed we tried to connect the camera but it wasn't getting detected we tried different commands to check the detection of camera such as 'vcgencmd get_camera'. Solution was to enable the camera from the interference settings.
- We also started working on our first simulation in 2D where the two main classes are Preception and Simulation which simulates the whole world.
- We completed all the necessary tasks given such as
- Task 1: Clean research files

Update and organize:

* research_problem_statement.md
* research_questions.md
* literature_matrix.xlsx or .csv
* paper_classification.md
* literature_summary.md
* research_gap_draft.md
* simulation_variables.md
* variable_metric_mapping.md
* proposed_simulation_plan.md
* expected_results_plan.md
* methodology_draft.md
* experiment_scenarios.md

Make sure all files follow the same research direction.

- Task 2: Improve research questions and hypotheses

In research_questions.md, make the questions measurable.

Example:

* How does increasing false positive rate affect unnecessary avoidance?
* How does increasing false negative rate affect collision risk?
* How does latency affect swarm response time?
* How does sensor dropout affect mission success?
* Does trust-weighted fusion reduce wrong swarm decisions compared to naive fusion?

Add 4–5 hypotheses.

Example:

* H1: Higher false negative rate increases collision risk.
* H2: Higher false positive rate increases unnecessary avoidance.
* H3: Higher latency increases response time.
* H4: Sensor dropout reduces mission success.
* H5: Trust-weighted fusion performs better than naive fusion.

- Task 3: Improve simulation prototype structure

Inside:
simulation_prototype/

Create/update:

* simple_swarm_sim.py
* simulation_config.json
* run_experiments.py
* metrics_analysis.py
* simulation_log.csv
* results_summary.csv
* initial_results_summary.md
* simulation_readme.md

Create folders:

* logs/
* results/
* plots/

- Task 4: Make simulation configurable

Update simulation_config.json.

Add:

* number of UAVs
* area size
* start positions
* goal position
* obstacle position
* UAV speed
* safety distance
* simulation duration
* false positive rate
* false negative rate
* sensor noise level
* latency steps
* dropout probability
* confidence error level
* fusion mode

Fusion mode should include:

* no fusion
* naive fusion
* trust-weighted fusion

- Task 5: Run repeated experiments

Run each scenario at least 3 times:

1. Baseline with no perception error
2. False positive scenario
3. False negative scenario
4. Sensor noise scenario
5. Latency scenario
6. Sensor dropout scenario
7. Confidence error scenario
8. Naive fusion scenario
9. Trust-weighted fusion scenario

For each scenario, save CSV logs separately.

Example:

* baseline_run1.csv
* baseline_run2.csv
* baseline_run3.csv
* false_positive_run1.csv
* false_positive_run2.csv
* false_positive_run3.csv

- Task 6: Log useful simulation data

CSV should include:

* time step
* UAV ID
* UAV position x
* UAV position y
* goal position
* actual obstacle position
* perceived obstacle position
* perception error type
* confidence value
* fusion mode
* action taken
* distance to nearest UAV
* distance to obstacle
* collision risk flag
* unnecessary avoidance flag
* missed response flag
* mission completed flag


- Task 7: Calculate metrics

In metrics_analysis.py, calculate:

* total collision-risk events
* total near misses
* unnecessary avoidance count
* missed response count
* mission success
* average response time
* average formation error if possible
* average confidence error if included

Create:
results_summary.csv

Columns:

* scenario
* run number
* false positive rate
* false negative rate
* noise level
* latency
* dropout probability
* fusion mode
* collision risk count
* unnecessary avoidance count
* missed response count
* mission success
* average response time
* average formation error

- Task 8: Generate basic plots

Create plots for:

* false positive rate vs unnecessary avoidance
* false negative rate vs collision risk
* latency vs response time
* dropout probability vs mission success
* fusion mode vs collision risk
* baseline vs all error scenarios

Save plots in:
simulation_prototype/plots/


- Task 9: Write initial result analysis

Update:
initial_results_summary.md

Add:

* scenarios tested
* number of runs
* metrics collected
* baseline result
* false positive result
* false negative result
* latency result
* dropout result
* which error caused the worst behavior
* what needs improvement in the prototype

- Task 10: Update methodology

Update:
methodology_draft.md

Add:

* prototype structure
* simulation flow
* how UAVs move
* how obstacle detection is simulated
* how false positives are injected
* how false negatives are injected
* how latency/dropout/noise are injected
* how metrics are calculated
* limitations of current prototype
* what will be improved later

## Challenges Faced: 
    1. We have to enable the camera through the interference settings but there was no option to enable the camera, we tried to resolve this issue by configuring the .config file but it didn't worked. The main problem was after re did everything we didn't update the OS it was still working on older version. The camera enable option was available on the new version thus we updated and upgraded the raspberry-config file and raspberry config-core file only.
    2. Had Problem in understanding the purpose of run_experiment file and how to  combine it with other files when the other .py files were deleivring all the required outputs.
