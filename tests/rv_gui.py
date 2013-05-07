import logging
from time import sleep
from autotest.client.shared import error
from virttest.aexpect import ShellCmdError


def run_rv_gui(test, params, env):
    
    tests = params.get("rv_gui_test_list").split()
    errors = 0
    
    guest_vm = env.get_vm(params["guest_vm"])
    guest_vm.verify_alive()
    guest_session = guest_vm.wait_for_login(
            timeout=int(params.get("login_timeout", 360)))

    client_vm = env.get_vm(params["client_vm"])
    client_vm.verify_alive()
    client_session = client_vm.wait_for_login(
            timeout=int(params.get("login_timeout", 360)))

    client_session.cmd("export DISPLAY=:0.0")
    client_session.cmd('. /home/test/.dbus/session-bus/`cat /var/lib/dbus/machine-id`-0')
    client_session.cmd('export DBUS_SESSION_BUS_ADDRESS DBUS_SESSION_BUS_PID DBUS_SESSION_BUS_WINDOWID')
    client_session.cmd("cd %s" % params.get("test_script_tgt"))
    logging.info("Executing gui tests: %s" % tests)
    for i in tests:
        logging.info("Test: %20s" % i)
        try:
            logging.info(client_session.cmd("./unittests/%s_rv.py" % i))
        except:
            logging.error("Status:         FAIL")
            errors +=1
        else:
            logging.info("Status:         PASS")
    if errors:
        raise error.TestFail("%d GUI tests failed, see log for more details" % errors)