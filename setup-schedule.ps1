# Create daily task at 10:00 AM

$TaskName = "MonsterHunterTracker_DailyUpdate"
$ScriptPath = "c:\Users\yuyingjiang\WorkBuddy\20260331101524\monster-hunter-tracker\scripts\update-data.js"
$ProjectPath = "c:\Users\yuyingjiang\WorkBuddy\20260331101524\monster-hunter-tracker"

# Remove existing task if any
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Create action
$Action = New-ScheduledTaskAction -Execute "node" -Argument "`"$ScriptPath`"" -WorkingDirectory $ProjectPath

# Create trigger - Daily at 10:00 AM
$Trigger = New-ScheduledTaskTrigger -Daily -At "10:00 AM"

# Create settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Monster Hunter Tracker Daily Update"

Write-Host "Task created: $TaskName"
Write-Host "Schedule: Daily at 10:00 AM"
