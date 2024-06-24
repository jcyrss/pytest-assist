import os

LIB_PATH = os.path.dirname(os.path.abspath(__file__))

class Testing_State:
    inTesting = False
    curTestName = ''
    saveRecord = False
    quitTesting = False

    te = None


class Settings:
    host = '0.0.0.0'
    http_port = 48530
    ws_port = 48531

    # don't change the following settings, in case of fatal files removing
    
    PTC_DIR  =     '.pytest_assist'
    RECORDS_DIR  = f'{PTC_DIR}/records'
    RULES_DIR    = f'{PTC_DIR}/rules_select'
    DOWNLAOD_DIR = f'{PTC_DIR}/download'

    
class LANG:
    cur = 0 # lang used

    en = 0
    zh = 1

 
import locale
if 'zh_CN' in locale.getdefaultlocale():
    LANG.cur = LANG.zh
else :
    LANG.cur = LANG.en

def L(*arg):
    return arg[LANG.cur]



REPORT_TEMPLATE_PATH = os.path.join(LIB_PATH, 'export_report.html')

with open(REPORT_TEMPLATE_PATH,'r',encoding='utf8') as f:
    REPORT_HTML_CONTENT = f.read()