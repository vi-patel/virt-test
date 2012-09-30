import wx

class MyForm(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Test")

        # Add a panel so it looks the correct on all platforms
        panel = wx.Panel(self, wx.ID_ANY)
        btn = wx.TextCtrl(panel, value="")

        btn.Bind(wx.EVT_CHAR, self.onCharEvent)
        btn.SetFocus()

        f = open("/tmp/autotest-rv_input", "w")
        f.write("")
        f.close()

    def onCharEvent(self, event):
        keycode = event.GetKeyCode()

        f = open("/tmp/autotest-rv_input", "a")
        f.write("%s," % str(keycode))
        f.close()
        event.Skip()

if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = MyForm()
    frame.Show()
    app.MainLoop()
