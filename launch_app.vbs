Set oWS = CreateObject("WScript.Shell")
Set oFSO = CreateObject("Scripting.FileSystemObject")

' 1. Lay thu muc chua chinh file script nay (Giup Tool hoat dong linh hoat o moi may tinh va o dia)
scriptDir = oFSO.GetParentFolderName(WScript.ScriptFullName)

' 2. Kiem tra xem TS_Origin_Control.exe da chay chua
Set oWMIService = GetObject("winmgmts:\\.\root\cimv2")
Set colProcesses = oWMIService.ExecQuery("Select * from Win32_Process Where Name = 'TS_Origin_Control.exe'")

If colProcesses.Count = 0 Then
    ' Uu tien tim TS_Origin_Control.exe ngay trong thu muc hien tai
    exePath = scriptDir & "\TS_Origin_Control.exe"
    exeDir = scriptDir
    
    ' Neu khong thay trong thu muc hien tai thi tim cac thu muc du phong
    If Not oFSO.FileExists(exePath) Then
        If oFSO.FileExists("C:\LDPlayer\dist\TS_Origin_Control.exe") Then
            exeDir = "C:\LDPlayer\dist"
            exePath = exeDir & "\TS_Origin_Control.exe"
        ElseIf oFSO.FileExists("C:\Users\Phat\Downloads\ldplayer_tool\dist\TS_Origin_Control.exe") Then
            exeDir = "C:\Users\Phat\Downloads\ldplayer_tool\dist"
            exePath = exeDir & "\TS_Origin_Control.exe"
        End If
    End If
    
    If oFSO.FileExists(exePath) Then
        oWS.CurrentDirectory = exeDir
        oWS.Run """" & exePath & """", 1, False
        ' Cho 1.5 giay de Tool va Web Server san sang o cong 8080
        WScript.Sleep 1500
    End If
End If

' 3. Bat Cua So Web App Dien Thoai (Tu dong chon Chrome hoac Microsoft Edge co san tren Windows)
chromePath1 = "C:\Program Files\Google\Chrome\Application\chrome.exe"
chromePath2 = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
edgePath1 = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
edgePath2 = "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
chromeArgs = "--app=http://localhost:8080 --window-size=510,720"

browserPath = ""
If oFSO.FileExists(chromePath1) Then
    browserPath = chromePath1
ElseIf oFSO.FileExists(chromePath2) Then
    browserPath = chromePath2
ElseIf oFSO.FileExists(edgePath1) Then
    browserPath = edgePath1
ElseIf oFSO.FileExists(edgePath2) Then
    browserPath = edgePath2
End If

If browserPath <> "" Then
    oWS.Run """" & browserPath & """ " & chromeArgs, 1, False
Else
    oWS.Run "http://localhost:8080", 1, False
End If
