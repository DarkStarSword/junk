~XButton2 & WheelDown::AltTab
~XButton2 & WheelUp::ShiftAltTab
~XButton2 & MButton::send "#{Tab}"

if not (A_IsAdmin) {
	A_TrayMenu.Add() ; Separator
	A_TrayMenu.Add("Elevate to Admin", elevate_permissions)
	; Win11 often opens the context menu behind the task bar. Add a handful of
	; dummy separators so our menu item will be high enough that won't matter:
	A_TrayMenu.Add()
	A_TrayMenu.Add()
	A_TrayMenu.Add()
	A_TrayMenu.Add()
	A_TrayMenu.Add()
	A_TrayMenu.Add()
}

elevate_permissions(ItemName, ItemPos, MyMenu)
{
	try {
		if A_IsCompiled
			Run '*RunAs "' A_ScriptFullPath '" /restart'
		else
			Run '*RunAs "' A_AhkPath '" /restart "' A_ScriptFullPath '"'
	}
	ExitApp
}
