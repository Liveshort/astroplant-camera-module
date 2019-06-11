# set this parameter to the level which you still want to print
SEVERITY = 3

# the defined levels
DBG_PRINT = 1
WRN_PRINT = 2
ERR_PRINT = 3
FTL_PRINT = 4

def d_print(str, lvl):
    if DBG_PRINT >= SEVERITY and lvl == DBG_PRINT:
        print("DEBUG: " + str)
    elif WRN_PRINT >= SEVERITY and lvl == WRN_PRINT:
        print("WARNING: " + str)
    elif ERR_PRINT >= SEVERITY and lvl == ERR_PRINT:
        print("ERROR: " + str)
    elif FTL_PRINT >= SEVERITY and lvl == FTL_PRINT:
        print("FATAL: " + str)
