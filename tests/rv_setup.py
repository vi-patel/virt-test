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
from virttest import utils_misc, utils_spice

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


def setup_vm(vm, params, test):
    """
    Setup the vm for GUI testing, install dogtail & move tests over.

    @param vm: a VM
    @param params: dictionary of test paramaters
    """
    vmparams = vm.get_params()
    ostype = vmparams.get("os_type")
    session = vm.wait_for_login(username = "root", password = "123456",
            timeout=int(params.get("login_timeout", 360)))
    if(ostype == "linux"):
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
    elif(ostype == "windows"):
        winqxl = params.get("winqxl")
        winvdagent = params.get("winvdagent")
        vioserial = params.get("vioserial")
        winp7 = params.get("winp7zip")
        guest_script_req = params.get("guest_script_req")
        guest_sr_dir = os.path.join("scripts", guest_script_req)
        guest_sr_path = utils_misc.get_path(test.virtdir, guest_sr_dir)
        winp7_path = os.path.join(test.virtdir, 'deps', winp7)
        winqxlzip = os.path.join(test.virtdir, 'deps', winqxl)
        winvdagentzip = os.path.join(test.virtdir, 'deps', winvdagent)
        vioserialzip = os.path.join(test.virtdir, 'deps', vioserial)
        #copy p7zip to windows and install it silently
        vm.copy_files_to(winp7_path, "C:\\")
        session.cmd_status("msiexec /i C:\\7z920-x64.msi /quiet") 
        #wait for p7zip to be installed
        #utils_spice.wait_timeout(5)
        outputpath = session.cmd("path")
        print outputpath

        #copy over the winqxl, winvdagent, virtio serial 
        vm.copy_files_to(winqxlzip, "C:\\")
        vm.copy_files_to(winvdagentzip, "C:\\")
        vm.copy_files_to(vioserialzip, "C:\\")
        vm.copy_files_to(guest_sr_path, "C:\\")
        #Wait for p7zip to be installed and all the files to be copied over
        utils_spice.wait_timeout(10)

        #extract winvdagent zip and start service
        session.cmd_status('"C:\\Program Files\\7-Zip\\7z.exe" e C:\\wvdagent.zip -oC:\\')
        session.cmd_status("C:\\vdservice.exe install")
        #wait for vdservice to come up
        utils_spice.wait_timeout(5)
        output = session.cmd("net start vdservice") 
        print output
        output = session.cmd("chdir")
        print output
        print "OUTPUT ABOVE --------------------->"

        #extract winqxl driver, place drivers in correct location & reboot
        #Note pnputil only works win 7+, need to find a way for win xp
        session.cmd_status('"C:\\Program Files\\7-Zip\\7z.exe" e C:\\vioserial.zip -oC:\\')
        output = session.cmd("C:\\Windows\\winsxs\\amd64_microsoft-windows-pnputil_31bf3856ad364e35_6.1.7600.16385_none_5958b438d6388d15\\PnPutil.exe -i -a C:\\vioser.inf")
        print "Virtio Serial status: " + output
        #Make sure virtio install is complete
        utils_spice.wait_timeout(5)

        #winqxl
        session.cmd_status('"C:\\Program Files\\7-Zip\\7z.exe" e C:\\wqxl.zip -oC:\\')
        output = session.cmd("C:\\Windows\\winsxs\\amd64_microsoft-windows-pnputil_31bf3856ad364e35_6.1.7600.16385_none_5958b438d6388d15\\PnPutil.exe -i -a C:\\qxl.inf")
        print "Win QXL status: " + output
        #Make sure qxl install is complete
        utils_spice.wait_timeout(5)
        vm.reboot()
         
        print "Setup for the Windows VM is complete"
    else:
        print "Not sure what OS is being setup"
        return(1)

def run_rv_setup(test, params, env):
    """
    Setup the VMs for remote-viewer testing

    @param test: QEMU test object.
    @param params: Dictionary with the test parameters.
    @param env: Dictionary with test environment.
    """

    for vm in params.get("vms").split():
        logging.info("Setting up VM: " + vm)
        setup_vm(env.get_vm(vm), params, test)
