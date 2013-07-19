import os, logging
from time import sleep
from autotest.client.shared import error
from virttest.aexpect import ShellCmdError
from virttest import utils_net, utils_spice

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

def getrvcorners(client_session, host_port, host_ip):
    rv_xinfo_cmd = "xwininfo -name 'spice://%s?port=%s (1) - Remote Viewer'" % (host_ip, host_port)
    rv_xinfo_cmd += " | grep Corners"
    try:
        rv_corners_raw = client_session.cmd(rv_xinfo_cmd)
        rv_corners = rv_corners_raw.strip()
        #print rv_res_raw
        #print rv_res
    except ShellCmdError:
        raise error.TestFail("Could not get the geometry of the rv window")
    except IndexError:
        raise error.TestFail("Could not get the geometry of the rv window")
    return rv_corners


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
    screenshot_dir = params.get("screenshot_dir")
    screenshot_name = params.get("screenshot_name")
    screenshot_exp_name = params.get("screenshot_expected_name")
    expected_rv_corners_fs = "Corners:  +0+0  -0+0  -0-0  +0-0"
    screenshot_exp_file = ""
    host_port = None
    guest_res = ""
    guest_res2 = ""
    rv_res = ""
    rv_res2 = ""
    rv_binary = params.get("rv_binary", "remote-viewer")

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
    rv_res_orig = getrvgeometry(client_session, host_port, host_ip)
    logging.info("Executing gui tests: %s" % tests)

    for i in tests:
        logging.info("Test: %20s" % i)        

        #Verification that needs to be done prior to running the gui test.
        if i in ("zoomin", "zoomout", "zoomnorm", "zoomin_shortcut", "zoomout_shortcut", "zoomnorm_shortcut"):
            #Get preliminary information needed for the zoom tests
            guest_res = getres(guest_session)
            rv_res = getrvgeometry(client_session, host_port, host_ip)

        # if i in ("screenshot"):
        if "screenshot" in i:
            screenshot_exp_file = os.path.join(screenshot_dir, screenshot_exp_name)
            try:
                client_session.cmd('[ -e ' + screenshot_exp_file +' ]')
                client_session.cmd('rm ' + screenshot_exp_file)
                print "Not expecting to get here, deleted: " + screenshot_exp_file
            except ShellCmdError:
                print screenshot_exp_name + " does not exist as expected."

        cmd = "./unittests/%s_rv.py" % i

        #Adding parameters to the test
        if (i == "connect"):
            cmd += " 'spice://%s:%s'" % (host_ip, host_port)

        #Run the test
        print "Running test: " + cmd
        try:
            logging.info(client_session.cmd(cmd))
        except:
            logging.error("Status:         FAIL")
            errors +=1
        else:
            logging.info("Status:         PASS")

        #Wait before doing any verification
        utils_spice.wait_timeout(5)


        #Verification Needed after the gui test was run
        if i in ("zoomin", "zoomout", "zoomnorm", "zoomin_shortcut", "zoomout_shortcut", "zoomnorm_shortcut"):
            guest_res2 = getres(guest_session)
            rv_res2 = getrvgeometry(client_session, host_port, host_ip)
            #Check to see that the resolution doesn't change
            logstr = "Checking that the guest's resolution doesn't change"
            checkresequal(guest_res, guest_res2, logstr)
            if i == "zoomin" or i == "zoomin_shortcut":
                #verify the rv window has increased
                errorstr = "Checking the rv window's size has increased"
                logging.info(errorstr)
                checkgeometryincrease(rv_res, rv_res2, errorstr)
            if i == "zoomout" or i == "zoomout_shortcut":
                #verify the rv window has decreased
                errorstr = "Checking the rv window's size has decreased"
                logging.info(errorstr)
                checkgeometryincrease(rv_res2, rv_res, errorstr)
            if i == "zoomnorm" or i == "zoomnorm_shortcut":
                errorstr = "Checking the rv window's size is the same as it was originally when rv was started."
                checkresequal(rv_res2, rv_res_orig, errorstr)

        if i in ("quit_menu", "quit_shortcut"):
            #Verify for quit tests that remote viewer is not running on client
            try:
                pidoutput = str(client_session.cmd("pgrep remote-viewer"))
                raise error.TestFail("Remote-viewer is still running on the client.")
            except ShellCmdError:
                logging.info("Remote-viewer process is not running as expected.")
        if "screenshot" in i:
            #Verify the screenshot was created and clean up
            try:
                client_session.cmd('[ -e ' + screenshot_exp_file + ' ]')
                client_session.cmd('rm ' + screenshot_exp_file)
                print screenshot_exp_name + " was created as expected"
            except ShellCmdError:
                raise error.TestFail("Screenshot " + screenshot_exp_file + " was not created")
        if i == "fullscreen" or i == "fullscreen_shortcut":
            #Verify that client's res = guests's res
            guest_res = getres(guest_session)
            client_res = getres(client_session)
            rv_geometry = getrvgeometry(client_session, host_port, host_ip)
            rv_corners = getrvcorners(client_session, host_port, host_ip)
            if(client_res == guest_res):
                logging.info("PASS: Guest resolution is the same as the client")
                #Verification #2, client's res = rv's geometry
                if(client_res == rv_geometry):
                    logging.info("PASS client's res = geometry of rv window")
                else:
                    raise error.TestFail("Client resolution: %s differs from the rv window's geometry: %s" %(client_res, rv_geometry))

            else:
                raise error.TestFail("Guest resolution: %s differs from the client: %s" %(guest_res, client_res))
            #Verification #3, verify the rv window is at the top corner
            if(rv_corners == expected_rv_corners_fs):
                logging.info("PASS: rv window is at the top corner: " + rv_corners)
            else:
                raise error.TestFail("rv window is not at the top corner as expected, it is at: " + rv_corners)
        #Verify rv window < client's res
        if i == "leave_fullscreen" or i == "leave_fullscreen_shortcut":
            rv_corners = getrvcorners(client_session, host_port, host_ip)
            if(rv_corners != expected_rv_corners_fs):
                logging.info("PASS: rv window is not at top corner as expected: " + rv_corners)
            else:
                raise error.TestFail("rv window is full screen, leaving full screen failed.")
            #rv_geometry = getrvgeometry(client_session, host_port, host_ip)
            #client_res = getres(client_session)
            #errorstr = "Checking that rv window's geometry is less than the client's resolution"
            #checkgeometryincrease(rv_geometry, client_res, errorstr)

        #Verify a connection is established
        if i == "connect":
            try:
                utils_spice.verify_established(client_vm, host_ip, host_port, rv_binary)
            except utils_spice.RVConnectError:
                raise error.TestFail("remote-viewer connection failed")

    if errors:
        raise error.TestFail("%d GUI tests failed, see log for more details" % errors)
