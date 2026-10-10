Add-Type -AssemblyName UIAutomationClient
$desktop = [System.Windows.Automation.AutomationElement]::RootElement
$wins = $desktop.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
Write-Host "Total desktop children: $($wins.Count)"
foreach ($w in $wins) {
    if ($w.Current.ProcessId -eq 2792) {
        Write-Host "PID 2792: '$($w.Current.Name)' Class: '$($w.Current.ClassName)'"
    }
}
