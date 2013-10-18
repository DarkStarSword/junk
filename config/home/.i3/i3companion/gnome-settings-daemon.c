#include <stdio.h>

int main(int argc, char *argv[])
{
	puts("This is a fake gnome-settings-daemon to satisfy /usr/share/acpi-support/policy-funcs.");
	puts("All this program does is fill up a slot in the process table. A DBus service is also");
	puts("required to trick it - that is implemented in i3companion's consolekit.py");
	puts("");
	puts("Honestly it would be better if there was just some way to register power managers...");
	getchar();
}
