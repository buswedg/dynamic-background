<#
.SYNOPSIS
Installs a single consolidated background scheduler task in Task Scheduler.

.DESCRIPTION
Registers a single scheduled task (DynamicBackground-LogOnOrSchedule-Run) under \Custom:
1. Trigger 1: Daily trigger starting at 12:00 AM, repeating every hour.
2. Trigger 2: Logon trigger to run 30 seconds after user logon.

All tasks are stored in \Custom.

.PARAMETER Config
Name of the JSON file (from the 'configs' directory) that defines the background schedule.

.OUTPUTS
Console output indicating success or failure of task registration.

.EXAMPLE
PS> .\Install-Task.ps1 -Config "default.json"
#>

[CmdletBinding()]
param (
    [string]$Config
)

#Requires -RunAsAdministrator

# --- Main Execution ---

try
{
    $ProjectRoot = $PSScriptRoot
    $TaskName = "Custom\DynamicBackground-LogOnOrSchedule-Run"
    $ScriptPath = "$PSScriptRoot\Background-Scheduler.ps1"

    Write-Host "`nRegistering task: $TaskName" -ForegroundColor Cyan

    # 1. Task settings
    $Settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -Priority 5

    # 2. Clean up existing task
    Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false

    # 3. Create consolidated triggers
    Write-Host "Creating task triggers..." -ForegroundColor Gray

    # Trigger 1: Daily repeat every 1 hour
    $DailyTrigger = New-ScheduledTaskTrigger -Daily -At 12:00am
    $DailyTrigger.Repetition = (New-ScheduledTaskTrigger -Once -At 12:00am -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Hours 23 -Minutes 59)).Repetition

    # Trigger 2: At Logon
    $LogonTrigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $LogonTrigger.Delay = "PT30S"

    $Triggers = @($DailyTrigger, $LogonTrigger)

    # 4. Define action to run Background-Scheduler.ps1 dynamically
    $ArgList = "--headless powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$ScriptPath`""
    $Action = New-ScheduledTaskAction -Execute "$env:windir\System32\conhost.exe" -Argument $ArgList

    # 5. Register the single consolidated task
    Write-Host "Registering consolidated scheduled task: $TaskName" -ForegroundColor Gray

    Register-ScheduledTask -Action $Action -Trigger $Triggers -Settings $Settings -TaskName $TaskName -User $env:USERNAME -Force | Out-Null

    Write-Host "`nSUCCESS: Task registered successfully: $TaskName" -ForegroundColor Green
}
catch
{
    Write-Host "An unexpected error occurred: $_" -ForegroundColor Red
}
