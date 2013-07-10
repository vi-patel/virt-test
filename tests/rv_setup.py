import logging
from autotest.client.shared import error
from virttest.aexpect import ShellCmdError
from time import sleep
from os import system, getcwd, chdir

def install_dogtail(session, rpm):
    logging.info("Installing dogtail from: %s" % rpm)
    session.cmd("yum -y localinstall %s" % rpm)
    if session.cmd_status("rpm -q dogtail"):
        raise Exception("Failed to install dogtail")

def deploy_tests(vm, params):
    logging.info("Deploying tests")
    old = getcwd()
    chdir(params.get("test_dir"))
    system("zip -r tests .")
    chdir(old)
    vm.copy_files_to("%s/tests.zip" % params.get("test_dir"), "/home/test/tests.zip")
    session = vm.wait_for_login(
            timeout = int(params.get("login_timeout", 360)))
    session.cmd("unzip -o /home/test/tests.zip -d %s" % params.get("test_script_tgt"))
    session.cmd("mkdir -p ~/.gconf/desktop/gnome/interface")
    logging.info("Disabling gconfd")
    session.cmd("gconftool-2 --shutdown")
    logging.info("Enabling accessiblity")
    session.cmd("cp ~/tests/%gconf.xml ~/.gconf/desktop/gnome/interface/")

    
def setup_vm(vm, params):
    session = vm.wait_for_login(username = "root", password = "123456",
            timeout=int(params.get("login_timeout", 360)))
    if session.cmd_status("rpm -q dogtail"):
        install_dogtail(session, params.get("dogtail_rpm"))
    deploy_tests(vm, params)

def run_rv_setup(test, params, env):
    for vm in params.get("vms").split():
        logging.info("Setting up VM: %s" % vm)
        setup_vm(env.get_vm(vm), params)

