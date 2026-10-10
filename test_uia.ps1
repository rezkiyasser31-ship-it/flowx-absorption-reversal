Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$proc = Get-Process -Name NinjaTrader -ErrorAction SilentlyContinue
if (-not $proc) {
    Write-Host "NinjaTrader process not found."
    exit
}

$desktop = [System.Windows.Automation.AutomationElement]::RootElement

# Find all windows owned by NinjaTrader
$allWindows = $desktop.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)

foreach ($win in $allWindows) {
    if ($win.Current.ProcessId -eq $proc.Id) {
        Write-Host "Found NT8 Window: '$($win.Current.Name)' Class: '$($win.Current.ClassName)'"
        if ($win.Current.Name -like "*Strategy Analyzer*") {
            Write-Host "  -> TARGET FOUND: Strategy Analyzer Window!"
            $runBtnCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, "Run")
            $runBtn = $win.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $runBtnCond)
            if ($runBtn) {
                Write-Host "  -> SUCCESS: Found 'Run' button!"
                Write-Host "  -> ControlType: $($runBtn.Current.ControlType.ProgrammaticName)"
            }
        }
    }
}
