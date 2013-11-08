//Check if number of passed arguments is 2 or 3
var oArgs = WScript.Arguments;
if (oArgs.Count() < 2 | oArgs.Count() > 3)
  showError();
else
  reportArgs(); 

//Shows error message
function showError()
{
  var timeout = 10;
  var title = "Error";
  var button = 48;
  var oWSH = WScript.CreateObject("WScript.Shell");
  var result = oWSH.Popup("Application name and/or revision number missing!\n\nThis window will close automatically in 10 seconds...", timeout, title, button);
  if (result == 1) { //Quit immediately after OK button was clicked
    WScript.Quit();
  }
  WScript.Quit(); //Quit anyway after timeout...
}

//Pass arguments via HTTP GET method to the compmgr.php script
function reportArgs()
{
  //Compose URL
  if (oArgs.Count() == 2)    
    var strURL = "http://ffdshow-tryout.sourceforge.net/compmgr.php?app=" + oArgs(0) + "&rev=" + oArgs(1);
  if (oArgs.Count() == 3)    
    var strURL = "http://ffdshow-tryout.sourceforge.net/compmgr.php?app=" + oArgs(0) + "&rev=" + oArgs(1) + "&type=" + oArgs(2);
    
  //Create IE object
  var oIE = WScript.CreateObject("InternetExplorer.Application", "IE_");

  //Customize IE window
  oIE.Left = 50;
  oIE.Top = 100;
  oIE.Height = 320;
  oIE.Width = 380;
  oIE.MenuBar = 0;
  oIE.ToolBar = 0;
  oIE.StatusBar = 0;

  //Finally open URL and show browser window
  oIE.Navigate(strURL);
  oIE.Visible = true;

  //Send scripting host to sleep
  WScript.Sleep(10000);

  //Close browser window after wscript.exe wakes up
  oIE.Quit();
}

//OnQuit-Event gets fired when browser window gets
//closed before (click on Close-button) or after timeout
function IE_OnQuit()
{
  WScript.Quit();
}
