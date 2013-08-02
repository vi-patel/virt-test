"""
A setup test to perform the preliminary actions that are required for
the rest of the tests.

Actions Currently Performed:
(1) installs dogtail on the client
(2) performs required setup to get dogtail tests to work
(2) puts the dogtail scripts onto the client VM

Requires: the client and guest VMs to be setup.
"""

import logging, os
from os import system, getcwd, chdir

def install_rpm(session, name, rpm):
    """
    installs dogtail on a VM

    @param session: cmd session of a VM
    @rpm: rpm to be installed
    @name name of the package
    
    """
    logging.info("Installing " + name + " from: " + rpm)
    session.cmd("yum -y localinstall %s" % rpm)
    if session.cmd_status("rpm -q " + name):
        raise Exception("Failed to install " +  name)

def deploy_tests(vm, params):
    """
    Moves the dogtail tests to a vm

    @param vm: a VM
    @param params: dictionary of paramaters
    """
    logging.info("Deploying tests")
    script_location = params.get("test_script_tgt")
    old = getcwd()
    chdir(params.get("test_dir"))
    system("zip -r tests .")
    chdir(old)
    vm.copy_files_to("%s/tests.zip" % params.get("test_dir"), \
                     "/home/test/tests.zip")
    session = vm.wait_for_login(
            timeout = int(params.get("login_timeout", 360)))
    session.cmd("unzip -o /home/test/tests.zip -d " + script_location)
    session.cmd("mkdir -p ~/.gconf/desktop/gnome/interface")
    logging.info("Disabling gconfd")
    session.cmd("gconftool-2 --shutdown")
    logging.info("Enabling accessiblity")
    session.cmd("cp ~/tests/%gconf.xml ~/.gconf/desktop/gnome/interface/")


def setup_vm(vm, params):
    """
    Setup the vm for GUI testing, install dogtail & move tests over.

    @param vm: a VM
    @param params: dictionary of test paramaters
    """
    session = vm.wait_for_login(username = "root", password = "123456",
            timeout=int(params.get("login_timeout", 360)))
    arch = params.get("vm_arch_name")
    fedoraurl = params.get("fedoraurl")
    wmctrl_64rpm = params.get("wmctrl_64rpm")
    wmctrl_32rpm = params.get("wmctrl_32rpm")
    dogtailrpm = os.path.join(fedoraurl, arch, params.get("dogtail_rpm"))
    if arch == "x86_64":
        wmctrlrpm = os.path.join(fedoraurl, arch, wmctrl_64rpm)
    else:
        wmctrlrpm = os.path.join(fedoraurl, arch, wmctrl_32rpm)
    if session.cmd_status("rpm -q dogtail"):
        install_rpm(session, "dogtail", dogtailrpm)
    if session.cmd_status("rpm -q wmctrl"):
        install_rpm(session, "wmctrl", wmctrlrpm)
    deploy_tests(vm, params)

def run_rv_setup(test, params, env):
    """
    Setup the VMs for remote-viewer testing

    @param test: QEMU test object.
    @param params: Dictionary with the test parameters.
    @param env: Dictionary with test environment.
    """

    for vm in params.get("vms").split():
        logging.info("Setting up VM: " + vm)
        setup_vm(env.get_vm(vm), params)
