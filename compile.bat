@echo off
echo Compiling FlowXAbsorptionReversal_ES...
"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /target:library /out:"C:\Users\yasser\.gemini\antigravity\scratch\trading\test_compile.dll" /reference:"C:\Program Files\NinjaTrader 8\bin\NinjaTrader.Core.dll" /reference:"C:\Program Files\NinjaTrader 8\bin\NinjaTrader.Gui.dll" /reference:"C:\Users\yasser\.gemini\antigravity\scratch\trading\NinjaTrader.Custom.ref.dll" /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\WPF\PresentationCore.dll" /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\WPF\PresentationFramework.dll" /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\WPF\WindowsBase.dll" /reference:"System.ComponentModel.DataAnnotations.dll" "C:\Users\yasser\Documents\NinjaTrader 8\bin\Custom\Strategies\FlowXAbsorptionReversal_ES.cs"
if errorlevel 1 exit /b 1

echo Compiling FlowXAbsorptionReversal_ES_LowFreq...
"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /target:library /out:"C:\Users\yasser\.gemini\antigravity\scratch\trading\test_compile_lowfreq.dll" /reference:"C:\Program Files\NinjaTrader 8\bin\NinjaTrader.Core.dll" /reference:"C:\Program Files\NinjaTrader 8\bin\NinjaTrader.Gui.dll" /reference:"C:\Users\yasser\.gemini\antigravity\scratch\trading\NinjaTrader.Custom.ref.dll" /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\WPF\PresentationCore.dll" /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\WPF\PresentationFramework.dll" /reference:"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\WPF\WindowsBase.dll" /reference:"System.ComponentModel.DataAnnotations.dll" "C:\Users\yasser\Documents\NinjaTrader 8\bin\Custom\Strategies\FlowXAbsorptionReversal_ES_LowFreq.cs"
if errorlevel 1 exit /b 1

echo ALL STRATEGIES COMPILED SUCCESSFULLY!
