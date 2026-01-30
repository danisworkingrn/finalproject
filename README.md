# Day 5 - Final Project
Scenario: You've been learning how to automate parts of the FIR Filter IP validation process. But how do you check the validation results?

You are now given a reference chip, `golden`, that you have to compare all units (`impl0` to `impl5`) against. `golden` represents the specifications and by comparing how each unit performs against `golden`, you can now check the compliance of each chip. There are 5 test cases (TC) to do for each chip - it passes if its performance is up to specification, i.e. the same as the `golden` chip.

***NOTE:*** **If running `./impl0` doesn't work, try `impl0`, `impl0.exe`, and `./impl0.exe`. If it still doesn't work for you on your laptop, you can try doing the assignment on the remote server. Check `/home/emmanuella.pv@oppstar.local/PYTHON_TRAINING/insts` (read the README!).**

## Assignment instructions
**See the attached `Final_Project.pdf`.**

You will need to test for these features on all the instances:
1. Global enable/disable
2. POR register values
3. Input buffer overflow and clearing
4. Filter bypassing
5. Signal processing

After executing all those tests on every instance, use the provided `validation_report.odt` template and make a report that contains:
- A proof of execution (ex: a screenshot of your script execution)
- A brief analysis on the execution result (ex: register field X does not match with the POR values …)
- A status of the test execution (pass/fail/wip)

Notice how we've been working on some of these tests. You can re-use code from the previous assignments. You can also make use of the starter code provided in `main.py`, but it is not mandatory - feel free to write your own code from scratch.

The following section describes each testcase further.

**Testcase 1: Global enable/disable**
- Our IP has a global enable signal which needs to be asserted to use the IP. When the global enable signal is de-asserted, the IP is expected to be inactive and will not respond to any stimuli.
- Passing criteria: IP channels except for the common channel is inaccessible when enable is de-asserted

**Testcase 2: POR register values**
- Power-on reset (POR) is mechanism in ICs where a reset signal is asserted when the power is first applied. Registers in the IP we are testing will be reset to their default values when a reset signal is asserted.
- Passing Criteria: All register values after reset matches with the values as specified in por.csv

**Testcase 3: Input buffer overflow and clearing**
- The FIR filter IP has an input buffer that stores sampled input signal when the filter is halted. It can store up to 255 samples before it loses data and can be cleared by setting the right register field.
- Passing Criteria: Input buffer count is correct, the correct register field is set upon overflow, and that the input buffer count can be cleared.

**Testcase 4: Filter bypassing**
- A register field in the instances can be set to bypass signal processing.
- Passing Criteria: Output signal matches exactly with the input signal when the bypass is enabled.

**Testcase 5: Signal processing**
- This is the main feature of the IP. You will need to set the filter’s coefficients and drive its input signal. You will be provided with a .cfg file that specifies the coef. values and enables. You will also be provided with a .vec file that contains values of the input signals to drive.
- Proof of execution requirement: A visualization of the input and output signals
- Passing Criteria: Output signals matches exactly with the output signals from the golden model given the same coefficients and input signals.

## Submitting the assignment
- Click "Fork" (upper right, above "Add file" and "Code") 
- Create fork without changing any of the settings
- Go to signal-processing.py and modify it according to the instructions.

Note: You can refer to `using-github-and-autograder.pdf` in `/home/emmanuella.pv@oppstar.local/PYTHON_TRAINING/` after you connect to Remote Server `10.80.10.25`. Although the "Using Autograder" part is no longer applicable since we are no longer using GitHub Classroom, the "Using GitHub" part is still applicable. 

