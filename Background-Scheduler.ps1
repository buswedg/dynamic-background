<#
.SYNOPSIS
Main entry point for the background scheduler.

.DESCRIPTION
Coordinates theme selection and background application.

.PARAMETER Config
Name of the JSON file (from the 'configs' directory) that contains the theme library and schedule.

.OUTPUTS
Console output and log file saved to %TEMP%\background-scheduler.log.

.EXAMPLE
PS> .\Background-Scheduler.ps1 -Config "default.json"
#>

[CmdletBinding()]
param (
    [string]$Config,
    [switch]$TrueRandom
)

# --- Configuration ---

$LogPath = Join-Path $env:TEMP "background-scheduler.log"
$ApplierPath = Join-Path $PSScriptRoot "Set-Background.ps1"
$ProjectRoot = $PSScriptRoot

# --- Function Definitions ---

function Resolve-PathRobust
{
    param ([string]$Target, [string]$Dir)
    if ([System.IO.Path]::IsPathRooted($Target)) { return $Target }
    return [System.IO.Path]::GetFullPath((Join-Path $Dir $Target))
}


# --- Main Execution ---

Start-Transcript -Path $LogPath -Append

try
{
    Write-Host "`n--- Background Scheduler Run: $(Get-Date) ---" -ForegroundColor Gray
    
    # 1. Resolve backgrounds library
    $BackgroundsJsonPath = Join-Path $ProjectRoot "data\backgrounds.json"
    if (-not (Test-Path $BackgroundsJsonPath))
    {
        Write-Host "Error: backgrounds.json not found at $BackgroundsJsonPath" -ForegroundColor Red
        Write-Host "Please run 'poetry run python -m dynamic_background.cli schedule' or 'run.bat schedule' first." -ForegroundColor Red
        return
    }

    try
    {
        $Library = Get-Content $BackgroundsJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch
    {
        Write-Host "Failed to parse backgrounds.json" -ForegroundColor Red
        return
    }

    # 2. Resolve schedule configuration
    $ConfigJsonPath = $null
    if ($Config -and (Test-Path $Config))
    {
        $ConfigJsonPath = $Config
    }
    else
    {
        $ConfigJsonPath = Join-Path $ProjectRoot "schedule.json"
    }

    $Schedule = $null
    if (Test-Path $ConfigJsonPath)
    {
        try
        {
            $ConfigData = Get-Content $ConfigJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $Schedule = $ConfigData.schedule
        }
        catch
        {
            Write-Host "Warning: Failed to parse schedule config. Defaulting to all-random." -ForegroundColor Yellow
        }
    }

    # 3. Determine theme
    $DayFull = (Get-Date).DayOfWeek.ToString()
    $DayShort = $DayFull.Substring(0, 3)
    $RawTheme = $null

    if ($Schedule)
    {
        if ($Schedule.$DayFull)
        {
            $RawTheme = $Schedule.$DayFull
        }
        elseif ($Schedule.$DayShort)
        {
            $RawTheme = $Schedule.$DayShort
        }
    }

    $LibraryThemes = @($Library.psobject.Properties.Name)

    if ($LibraryThemes.Count -eq 0)
    {
        Write-Host "Error: No themes found in backgrounds library." -ForegroundColor Red
        return
    }

    function Resolve-ThemeSelection
    {
        param ($Selection)
        if ($null -eq $Selection) { return $null }

        $SelectionList = @($Selection)
        # Check if list/array
        if ($Selection -is [System.Collections.IList] -or ($Selection -is [array] -and -not ($Selection -is [string])) -or $SelectionList.Count -gt 1)
        {
            if ($TrueRandom)
            {
                $Chosen = $SelectionList | Get-Random
            }
            else
            {
                $Seed = [int](Get-Date -Format "yyyyMMdd")
                $Index = Get-Random -Minimum 0 -Maximum $SelectionList.Count -SetSeed $Seed
                $Chosen = $SelectionList[$Index]
            }
            Write-Host "Resolved theme list to: $Chosen" -ForegroundColor Cyan
            return $Chosen
        }

        return $Selection
    }

    $ThemeName = Resolve-ThemeSelection -Selection $RawTheme

    if ($null -eq $ThemeName)
    {
        if ($TrueRandom)
        {
            $ThemeName = $LibraryThemes | Get-Random
        }
        else
        {
            $Seed = [int](Get-Date -Format "yyyyMMdd")
            $Index = Get-Random -Minimum 0 -Maximum $LibraryThemes.Count -SetSeed $Seed
            $ThemeName = $LibraryThemes[$Index]
        }
        Write-Host "Day: $DayFull (Unmapped) -> Randomly chosen theme (Deterministic): $ThemeName" -ForegroundColor Cyan
    }
    else
    {
        Write-Host "Day: $DayFull -> Scheduled theme: $ThemeName" -ForegroundColor Cyan
    }


    # 4. Resolve theme triggers path
    $ThemePath = $Library.$ThemeName
    if ($null -eq $ThemePath)
    {
        Write-Host "Error: Theme '$ThemeName' not found in library." -ForegroundColor Red
        return
    }

    $TriggersPath = Resolve-PathRobust -Target $ThemePath -Dir $ProjectRoot
    if (-not (Test-Path $TriggersPath))
    {
        Write-Host "Error: Triggers file not found: $TriggersPath" -ForegroundColor Red
        return
    }

    # 5. Call applier
    if (-not (Test-Path $ApplierPath))
    {
        Write-Host "Error: Applier script not found: $ApplierPath" -ForegroundColor Red
        return
    }

    Write-Host "Applying background triggers from: $TriggersPath" -ForegroundColor Cyan
    & $ApplierPath -Trigger $TriggersPath
    
    Write-Host "--- Background Scheduler Run Complete ---" -ForegroundColor Gray
}
catch
{
    Write-Host "Critical Orchestration Error: $_" -ForegroundColor Red
}
finally
{
    Stop-Transcript
}
