import logging
from time import sleep
from autotest.client.shared import error
from virttest.aexpect import ShellCmdError
from virttest import utils_net

def getres(guest_session):
    try:
        guest_session.cmd("xrandr | grep '*' >/tmp/res")
        guest_res_raw = guest_session.cmd("cat /tmp/res|awk '{print $1}'")
        guest_res = guest_res_raw.split()[0]
    except ShellCmdError:
        raise error.TestFail("Could not get guest resolution, xrandr output:" +
                             " %s" % guest_res_raw)
    except IndexError:
        raise error.TestFail("Could not get guest resolution, xrandr output:" +
                             " %s" % guest_res_raw)
    return guest_res

def getrvgeometry(client_session, host_port, host_ip):
    rv_xinfo_cmd = "xwininfo -name 'spice://%s?port=%s (1) - Remote Viewer'" % (host_ip, host_port)
    rv_xinfo_cmd += " | grep geometry"
    try:
        rv_res_raw = client_session.cmd(rv_xinfo_cmd)
        rv_res_raw = rv_res_raw.split('+')[0]
        rv_res = rv_res_raw.split()[1]
        #print rv_res_raw
        #print rv_res
    except ShellCmdError:
        raise error.TestFail("Could not get the geometry of the rv window")
    except IndexError:
        raise error.TestFail("Could not get the geometry of the rv window")
    return rv_res

def checkgeometryincrease(rv_res, rv_res2, errorstr):
    #Verify the height of has increased
    if(int(rv_res.split('x')[0]) < int(rv_res2.split('x')[0])):
        logging.info("Height check was successful")
    else:
        raise error.TestFail("Checking height: " + errorstr)
    #Verify the width of rv window increased after zooming in
    #The second split of - is a workaround because the xwinfo sometimes
    #prints out dashes after the resolution for some reason.
    if(int(rv_res.split('x')[1].split('-')[0]) < int(rv_res2.split('x')[1].split('-')[0])):
        logging.info("Width check was successful")
    else:
        raise error.TestFail("Checking width: " + errorstr)

def checkresequal(res1, res2, logmessage):
    #Verify the resolutions are equal
    logging.info(logmessage)
    if res1 == res2:
        pass
    else:
        raise error.TestFail("Resolution of the guest has changed")

def run_rv_gui(test, params, env):
    #Get required paramters 
    host_ip = utils_net.get_host_ip_address(params)
    host_port = None
    guest_res = ""
    guest_res2 = ""
    rv_res = ""
    rv_res2 = ""

    tests = params.get("rv_gui_test_list").split()
    errors = 0
    
    guest_vm = env.get_vm(params["guest_vm"])
    guest_vm.verify_alive()
    guest_session = guest_vm.wait_for_login(
            timeout=int(params.get("login_timeout", 360)))
    #update host_port
    host_port = guest_vm.get_spice_var("spice_port")

    client_vm = env.get_vm(params["client_vm"])
    client_vm.verify_alive()
    client_session = client_vm.wait_for_login(
            timeout=int(params.get("login_timeout", 360)))

    client_session.cmd("export DISPLAY=:0.0")
    guest_session.cmd("export DISPLAY=:0.0")
    client_session.cmd('. /home/test/.dbus/session-bus/`cat /var/lib/dbus/machine-id`-0')
    client_session.cmd('export DBUS_SESSION_BUS_ADDRESS DBUS_SESSION_BUS_PID DBUS_SESSION_BUS_WINDOWID')
    client_session.cmd("cd %s" % params.get("test_script_tgt"))

    logging.info("Executing gui tests: %s" % tests)

    for i in tests:
        logging.info("Test: %20s" % i)        
        if i in ("zoomin", "zoomout"):
            #Get preliminary information needed for the zoom tests
            guest_res = getres(guest_session)
            rv_res = getrvgeometry(client_session, host_port, host_ip)
        try:
            logging.info(client_session.cmd("./unittests/%s_rv.py" % i))
        except:
            logging.error("Status:         FAIL")
            errors +=1
        else:
            logging.info("Status:         PASS")

        if i in ("zoomin", "zoomout"):
            guest_res2 = getres(guest_session)
            rv_res2 = getrvgeometry(client_session, host_port, host_ip)
            #Check to see that the resolution doesn't change
            logstr = "Checking that the guest's resolution doesn't change"
            checkresequal(guest_res, guest_res2, logstr)
            if i == "zoomin":
                #verify the rv window has increased
                errorstr = "Checking the rv window's resolution has increased"
                logging.info(errorstr)
                checkgeometryincrease(rv_res, rv_res2, errorstr)
            if i == "zoomout":
                #verify the rv window has decreased
                errorstr = "Checking the rv window's resolution has decreased"
                logging.info(errorstr)
                checkgeometryincrease(rv_res2, rv_res, errorstr)
        if i in ("quit_menu", "quit_shortcut"):
            #Verify for quit tests that remote viewer is not running on client
            try:
                pidoutput = str(client_session.cmd("pgrep remote-viewer"))
                raise error.TestFail("Remote-viewer is still running on the client.")
            except ShellCmdError:
                logging.info("Remote-viewer process is not running as expected.")
        
    if errors:
        raise error.TestFail("%d GUI tests failed, see log for more details" % errors)
