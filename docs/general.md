You should have blocked the STEP, installed the required tools before unblocking - so provide the STEPS to check if tools are actually installed, later you will provide the STEPS to install the needed tools and rollback to the STEP to test using the installed tools. Add cleanup STEPS if needed and verify no related artifacts are present after clean except they are needed for future tasks.

STEPS should be in this format:

# Diagnostic_<blocked STEP #> - <TITLE>

## STEP 1 - <TITLE>
### <Actual diagnostic, test, run etc>
### <Expected results, feedback, output etc>


## STEP 2 - <TITLE>
### <Actual diagnostic, test, run etc>
### <Expected results, feedback, output etc>
---

# Installation_<blocked STEP #> - <TITLE>

## STEP 1 - <TITLE>
### <Actual installation, test, run etc>
### <Expected results, feedback, output etc>
## STEP 2 - <TITLE>
### <Actual installation, test, run etc>
### <Expected results, feedback, output etc>

# Resume <blocked STEP #>
