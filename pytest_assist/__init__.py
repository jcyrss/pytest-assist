import os, datetime
from .shared import Testing_State

def log_str(*args, sep=' ', end='\n', color=None, weight=None):
    """
    print information in log and report.
    This will not show in terminal window.

    Parameters
    ----------
    args : object to write to report
    sep  : the char to join the strings of args objects, default is space char
    end  : the end char of the content, default is new line char.
    color  : the color of the text in report, could be any value of CSS color. default is lightblack
    weight : the font weight of the text in report, could be any value of CSS font weight. 
    """    
    if not Testing_State.te:
        print('log_str function only available during pytest running')
        return
        
    logStr = sep.join([str(arg) for arg in args]) + end

    # t/s/c/w stands for text/string/color/weight
    item = {'t':'txt', 's':logStr}
    if color :
        item['c'] = color 
    if weight :
        item['w'] = weight

    Testing_State.te.logItems.append(item)

def log_str_red(*args, sep=' ', end='\n', weight=None):
    log_str(*args, sep=sep, end=end, color='red', weight=weight)

def log_str_green(*args, sep=' ', end='\n', weight=None):
    log_str(*args, sep=sep, end=end, color='green', weight=weight)

def log_str_blue(*args, sep=' ', end='\n', weight=None):
    log_str(*args, sep=sep, end=end, color='blue', weight=weight)

_STEP_NUM_COLOR = 'green'
def log_step(step_no:int, *args, sep=' '):
    """
    print information about test steps in log and report .
    This will not show in terminal window.


    Parameters
    ----------
    stepno : step number
    args : object to write to report
    sep  : the char to join the strings of args objects, default is space char
    """
    if not Testing_State.te:
        print('log_step function only available during pytest running')
        return
    Testing_State.te.logItems.append({'t':'txt', 's': f'\nStep #{step_no}' + "  ", 'c': _STEP_NUM_COLOR})
    Testing_State.te.logItems.append({'t':'txt', 's': sep.join([str(arg) for arg in args]) + '\n\n', 'c': _STEP_NUM_COLOR})



def selenium_screenshot(driver):
    """
    add screenshot image of browser into test report when using Selenium

    Parameters
    ----------
    driver: selenium webdriver
    """
    if not Testing_State.te:
        print('selenium_screenshot function only available during pytest running')
        return
    
    os.makedirs(Testing_State.te.recordImgDir,exist_ok=True)

    filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    filepath = f'{Testing_State.te.recordImgDir}/{filename}.png'

    driver.get_screenshot_as_file(filepath)

    # filepath_relative_to_log = f'/{filepath}'.replace('\\','/')

    Testing_State.te.logItems.append({'t':'img', 'src':f'{filename}.png'})

