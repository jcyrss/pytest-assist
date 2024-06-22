import sys, platform, time, argparse, json, os, pytest, datetime
from dataclasses import dataclass,field
from typing import List

from .servers import broadcastToClients, registClientMsgHandler, EnhancedJSONEncoder

from .shared import Testing_State, Settings, L

def _getWindowsVersion():
    version = platform.release()

    # refer to https://stackoverflow.com/q/68899983
    if  version == '10':
        version = 11 if sys.getwindowsversion().build >= 22000 else 10
    
    return f'Windows {version}'

def _broadcastTCExec(event, info:dict):
    broadcastToClients({
        'event': event,
        **info
    })


@dataclass
class _CaseResult:
    idx      : int
    nodeid   : str    
    ret_s  : str = ''  # setup phase result, 
    ret_c  : str = ''  # call phase result, 
    ret_t  : str = ''  # teardown phase result
    sct     : List = field(default_factory=list)
    # wrong   : bool = False

@dataclass
class _Stats:
    total     : int = 0
    deselected: int = 0
    rtotal    : int = 0
    executed  : int = 0
    passed    : int = 0
    failed    : int = 0
    skipped   : int = 0
    xfailed   : int = 0
    xpassed   : int = 0
    st_error  : int = 0  # including setup/teardown errors and collection errors

    def __getitem__(self, key):
        return getattr(self, key)
        
    def __setitem__(self, key, value):
        return setattr(self, key, value)


@dataclass
class _TestExec:
    name      : str = ''
    duration  : float = -1
    start_time: float = -1
    end_time : float = -1
    stats     : _Stats = field(default_factory=_Stats) 
    results   : List[_CaseResult] = field(default_factory=list)
    collect_errors   : List[str] = field(default_factory=list)


    def __post_init__(self) -> None:
        self.curIdx = -1
        
        self.start_time = time.time()

        # for case exec phase:setup/call/teardown, this is for saving log info
        self.logItems = None

        if not self.name:
            self.name = time.strftime('%Y%m%d-%H%M%S', time.localtime(self.start_time))
 
        if Testing_State.saveRecord:
            recordDir = os.path.join(Settings.RECORDS_DIR, self.name)       

            self.recordImgDir = os.path.join(recordDir, 'imgs')
            self.recordFilePath   = os.path.join(recordDir, 'record.json')

            os.makedirs(recordDir, exist_ok=True)


te = None
def _createTE():
    global te
    # print('** create TestExec')
    te = _TestExec(Testing_State.curTestName)      
    Testing_State.te = te

#  refer to the Flowchart of pytest plugin hook
#  https://github.com/pytest-dev/pytest/issues/3261#issuecomment-755461808
# https://docs.pytest.org/en/latest/reference/reference.html#pytest.hookspec.pytest_runtest_protocol

#  https://docs.pytest.org/en/7.1.x/reference/reference.html#hooks

def pytest_addoption(parser):
    def str2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')
    
    # group = parser.getgroup("terminal reporting")
    parser.addoption(
        "--waitforclient",
        action="store",
        dest="waitforclient",
        type=str2bool,
        default=False,
        help="whether wait for client to connect.",
    )

def pytest_configure(config):
    
    Testing_State.inTesting = True

    _createTE()

    # if sys.platform == 'win32':
    #     os_info = _getWindowsVersion()
    # else:
    #     os_info = platform.platform()

    # python_info = f'{sys.executable}({platform.python_version()})'
    # logInfo(os_info, python_info, sep=' ; ')
    # logInfo('rootdir:', config.rootpath, end='\n\n')


    # waitforclient = config.getoption("waitforclient")
    # # print('waitforclient', waitforclient)

    # if waitforclient:
    #     # wait for clients to connect
    #     while not wsc_clients:
    #         print('w')
    #         time.sleep(1)
    

def _saveTestRecord():    
    if Testing_State.saveRecord:
        te.start_time = time.strftime('%Y%m%d %H:%M:%S',time.localtime(te.start_time))
        te.end_time  = time.strftime('%Y%m%d %H:%M:%S',time.localtime(te.end_time))

        with open(te.recordFilePath, 'w', encoding='utf8') as f:
            json.dump(te, f, cls=EnhancedJSONEncoder, 
                      ensure_ascii=False, indent=2)

def pytest_unconfigure(config):
    global te
    
    Testing_State.inTesting = False

    te.end_time = time.time()

    try:
        _saveTestRecord()
    except:
        pass
    
    _broadcastTCExec('test-session-end', {
        'name'       : te.name,
        'end_time'   : te.end_time,
        'duration'   : te.duration
    })

    te = None

def pytest_deselected(items):
    
    deselected = len(items)
    # print(f'!! deselected {deselected} ' )

    te.stats.deselected += deselected

def pytest_collection_modifyitems(config, items):
    total = len(items)
    te.stats.total = total

    # print(f'totally {total} cases to run.' , end='\n\n')


def pytest_runtestloop(session):
    te.stats.rtotal = te.stats.total - te.stats.deselected

    # print(f'cases to run: {total}, total: {te.stats.total} , deselected: {te.stats.deselected} ' , end='\n\n')

    _broadcastTCExec('run-test-loop', {
        'name'       : te.name,
        'start_time' : time.strftime('%Y%m%d %H:%M:%S',time.localtime(te.start_time)),
        'working_dir': os.getcwd(),
        'stats'     : te.stats
    })

    

# refer to  https://docs.pytest.org/en/latest/reference/reference.html#pytest.hookspec.pytest_runtest_protocol
# *** one-case-begin ****
def pytest_runtest_logstart(nodeid, location):

    # print(f'\n\n--runtest_logstart->', nodeid)

    _broadcastTCExec('one-case-begin', {
        'nodeid'  : nodeid 
    })

    te.curIdx += 1
    result = _CaseResult(te.curIdx, nodeid)
    te.results.append(result)
       

# *** one-case-end ****
def pytest_runtest_logfinish(nodeid, location):

    # print(f'\n\n--runtest_logfinish->', nodeid)

    # results = te.results[-1]
    # if any([r['reprtext'] for r in results.sct]):
    #     results.wrong = True

    te.duration = round(time.time() - te.start_time, 3) # at most 3 digits 

    te.stats.executed += 1
    _broadcastTCExec('one-case-end', {
        'result'     : te.results[-1],
        'stats'      : te.stats
    })

       
    if Testing_State.quitTesting:
        Testing_State.quitTesting = False

        _broadcastTCExec('result.abort_testing',{
            'ret'   : 0,
            'info'  : L('Current test is aborted.', '当前测试被中止')
        })

        pytest.exit(L('User terminated testing.', "用户中止测试"))



def pytest_runtest_setup(item):
    te.logItems = [] 

def pytest_runtest_call(item):
    te.logItems = [] 

def pytest_runtest_teardown(item, nextitem):
    te.logItems = [] 

_case_previous_output = ''        
def  pytest_runtest_logreport(report):
    
    def process_outcome(report,resultsObj):
        if report.when == "setup":
            if report.outcome == "failed":
                ret = 'error'
                te.stats.st_error += 1
            else:
                ret = 'ok'

            resultsObj.ret_s = ret
            
        elif report.when == "teardown":
            if report.outcome == "failed":
                ret = 'error'
                te.stats.st_error += 1
            else:
                ret = 'ok'
                
            resultsObj.ret_t = ret
        
        else: # call 
            ret = report.outcome
            if hasattr(report, "wasxfail"):
                if report.outcome in ["passed", "failed"]:
                    te.stats.xpassed += 1
                    ret =  "xpassed"
                if report.outcome == "skipped":
                    te.stats.xfailed += 1
                    ret =  "xfailed"
                
            te.stats[report.outcome] += 1
            resultsObj.ret_c =  ret
        
        return ret

   
    global _case_previous_output, te

    # print(report.when, 'duration:', report.duration, 'outcome:',report.outcome)
    # due to the output of 'call' or 'teardown'  contains the output of the previous stages 
    if report.when == 'setup':            
        output = report.capstdout
    # when is 'call' or 'teardown'             
    else: 
        output = report.capstdout[len(_case_previous_output):]

    _case_previous_output = report.capstdout
      
    # on-going stats
    outcome = process_outcome(report,resultsObj=te.results[-1])

    one_report = {
        'when'      : report.when,
        'outcome'   : outcome,
        'duration'  : round(report.duration, 3), # at most 3 digits 
        'logs'      : te.logItems,
        'reprtext'  : report.longreprtext,
        'output'    : output,
    }

    sct = te.results[-1].sct
    sct.append(one_report)



def pytest_terminal_summary(terminalreporter, exitstatus):
    
    te.exitcode = exitstatus
    te.duration = round(time.time() - terminalreporter._sessionstarttime, 3) # at most 3 digits   
    
    te.stats.passed = len(terminalreporter.stats.get('passed', []))
    te.stats.failed = len(terminalreporter.stats.get('failed', []))
    te.stats.xfailed = len(terminalreporter.stats.get('xfailed', []))
    te.stats.skipped = len(terminalreporter.stats.get('skipped', []))
    errors = terminalreporter.stats.get('error', [])
    te.stats.errors = len(errors)

    for err in errors:
        if '<CollectReport' in repr(err):
            # print(err.longrepr)
            te.collect_errors.append(str(err.longrepr))

    _broadcastTCExec('pytest_terminal_summary',{
                'stats'   : te.stats,
                'collect_errors' : te.collect_errors
            })
    # print("************ exitstatus ********** ", exitstatus)
    


def _query_current_testing_state(msg):
    toIdx = msg['toIdx']
    ret =  {
        'event'      : 'result.current-testing-state',
        'name'       : te.name,
        'working_dir': os.getcwd(),
        'start_time' : time.strftime('%Y%m%d %H:%M:%S',time.localtime(te.start_time)),
        'results'    : te.results[:toIdx],
    }

    return ret

registClientMsgHandler(
    'query_current_testing_state',
    _query_current_testing_state)

