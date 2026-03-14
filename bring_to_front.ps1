Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    public const int SW_RESTORE = 9;
}
'@

Get-Process python | Where-Object { $_.MainWindowTitle -like '*PdfToolsXc*' } | ForEach-Object {
    [Win32]::ShowWindow($_.MainWindowHandle, [Win32]::SW_RESTORE)
    [Win32]::SetForegroundWindow($_.MainWindowHandle)
    Write-Host "Window brought to front"
}
