"""
rv_fullscreen.py - remote-viewer full screen
                   Testing the remote-viewer --full-screen option
                   If successfull, the resolution of the guest will
                   take the resolution of the client.

Requires: connected binaries remote-viewer, Xorg, gnome session

"""
import logging, os
from autotest.client.shared import error


def run_rv_fullscreen(test, params, env):
    """
    Tests the --full-screen option
    Positive test: full_screen parameter = True
    Negative test: full_screen parameter = False

    @param test: KVM test object.
    @param params: Dictionary with the test parameters.
    @param env: Dictionary with test environment.
    """
    # Get the parameters needed for the test
    full_screen = params.get("full_screen")
    guest_vm = env.get_vm(params["guest_vm"])
    client_vm = env.get_vm(params["client_vm"])

    guest_vm.verify_alive()
    guest_session = guest_vm.wait_for_login(
            timeout=int(params.get("login_timeout", 360)))

    client_vm.verify_alive()
    client_session = client_vm.wait_for_login(
            timeout=int(params.get("login_timeout", 360)))

    # Get the resolution of the client & guest
    logging.info("Getting the Resolution on the client")
    client_session.cmd("export DISPLAY=:0.0")
    client_res = client_session.cmd("xrandr | grep '*'")

    logging.info("Getting the Resolution on the guest")
    guest_session.cmd("export DISPLAY=:0.0")
    guest_res = guest_session.cmd("xrandr | grep '*'")

    logging.info("Here's the information I have: ")
    logging.info("\nClient Resolution: " + client_res)
    logging.info("\nGuest Resolution: " + guest_res)
    logging.info("\nFormatted Client Resolution: " + client_res.split()[0])
    logging.info("\nFormatted Guest Resolution: " + guest_res.split()[0])

    # Positive Test, verify the guest takes the resolution of the client
    if full_screen == "True":
        if(client_res.split()[0] == guest_res.split()[0]):
            logging.info("PASS: GUEST RESOLUTION IS THE SAME AS THE CLIENT")
        else:
            raise error.TestFail("GUEST RESOLUTION DIFFERS FROM THE CLIENT")
    # Negative Test, verify the resolutions are not equal
    elif full_screen == "False":
        if(client_res.split()[0] != guest_res.split()[0]):
            logging.info("PASS: GUEST RESOLUTION DIFFERS FROM THE CLIENT")
        else:
            raise error.TestFail("GUEST RESOLUTION IS THE SAME AS THE CLIENT")
    else:
        raise error.TestFail("The test setup is incorrect.")

    client_session.close()
    guest_session.close()
